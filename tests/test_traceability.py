import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "requirements.md"


def traceability_errors(markdown, root, required=()):
    known = {int(number) for number in re.findall(r"^\| T(\d+) \|", markdown, re.M)}
    rows = re.findall(r"^\| (N?FR-\d+) \|(.+)$", markdown, re.M)
    ids = [requirement for requirement, _ in rows]
    if not rows:
        return ["No FR/NFR rows."]
    errors = []
    if missing := set(required) - set(ids):
        errors.append(f"Missing requirements: {sorted(missing)}")
    if len(ids) != len(set(ids)):
        errors.append("Duplicate requirement ID.")
    for requirement, row in rows:
        cells = [cell.strip() for cell in row.rstrip("|").split("|")]
        if len(cells) != 6 or not all(cells):
            errors.append(f"{requirement}: missing traceability fields")
            continue
        _, modules, _, tests, status, evidence = cells
        paths = re.findall(r"`([^`]+\.py)`", modules)
        if not paths or any(not (root / path).is_file() for path in paths):
            errors.append(f"{requirement}: missing module or test file")
        ranges = re.findall(r"T(\d+)(?:–T(\d+))?", tests)
        if any(last and int(last) < int(first) for first, last in ranges):
            errors.append(f"{requirement}: reversed test range")
        numbers = {
            n
            for first, last in ranges
            for n in range(int(first), int(last or first) + 1)
        }
        if not numbers:
            errors.append(f"{requirement}: missing test IDs")
        elif unknown := numbers - known:
            errors.append(f"{requirement}: unknown test IDs {sorted(unknown)}")
        if status not in {"Verified (synthetic)", "Partial", "Planned"}:
            errors.append(f"{requirement}: invalid status")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", evidence)
        if not links or any(
            not (root / link.split("#")[0]).is_file() for link in links
        ):
            errors.append(f"{requirement}: missing local evidence")
    return errors


def test_all_requirements_trace_to_known_cases_and_evidence():
    baseline = {f"FR-{n:02}" for n in range(1, 9)} | {
        f"NFR-{n:02}" for n in range(1, 5)
    }
    assert traceability_errors(MATRIX.read_text(encoding="utf-8"), ROOT, baseline) == []


@pytest.mark.parametrize(
    ("tests", "target", "message"),
    [
        ("T01–T02", "exists.md", "unknown test IDs [2]"),
        ("T01", "missing.md", "missing local evidence"),
        ("T01、T78–T77", "exists.md", "reversed test range"),
    ],
)
def test_traceability_detects_broken_references(tmp_path, tests, target, message):
    (tmp_path / "exists.md").touch()
    (tmp_path / "module.py").touch()
    example = f"| FR-01 | description | `module.py` | source | {tests} | Partial | [report]({target}) |\n"
    assert traceability_errors(example + "| T01 | case |\n", tmp_path) == [
        f"FR-01: {message}"
    ]


def test_traceability_detects_removed_requirement_and_nonexistent_module(tmp_path):
    (tmp_path / "exists.md").touch()
    example = "| FR-01 | description | `missing.py` | source | T01 | Partial | [report](exists.md) |\n"
    assert traceability_errors(example + "| T01 | case |\n", tmp_path, {"FR-06"}) == [
        "Missing requirements: ['FR-06']",
        "FR-01: missing module or test file",
    ]
