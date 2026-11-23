import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "requirements.md"


def traceability_errors(markdown, root):
    known = {int(number) for number in re.findall(r"^\| T(\d+) \|", markdown, re.M)}
    rows = re.findall(r"^\| (N?FR-\d+) \|(.+)$", markdown, re.M)
    errors = []
    if not rows:
        return ["No FR/NFR rows."]
    for requirement, row in rows:
        cells = [cell.strip() for cell in row.rstrip("|").split("|")]
        if len(cells) != 6 or not all(cells):
            errors.append(f"{requirement}: missing traceability fields")
            continue
        _, modules, _, tests, status, evidence = cells
        if not re.search(r"`[^\x60]+\.py`", modules):
            errors.append(f"{requirement}: missing module or test file")
        ranges = re.findall(r"T(\d+)(?:–T(\d+))?", tests)
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
    assert traceability_errors(MATRIX.read_text(encoding="utf-8"), ROOT) == []


@pytest.mark.parametrize(
    ("tests", "target", "message"),
    [
        ("T01–T02", "exists.md", "unknown test IDs [2]"),
        ("T01", "missing.md", "missing local evidence"),
    ],
)
def test_traceability_detects_broken_references(tmp_path, tests, target, message):
    (tmp_path / "exists.md").touch()
    example = f"| FR-01 | description | `module.py` | source | {tests} | Partial | [report]({target}) |\n"
    assert traceability_errors(example + "| T01 | case |\n", tmp_path) == [
        f"FR-01: {message}"
    ]
