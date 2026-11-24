import csv
import hashlib
import json

import pytest

from research.annotation import CASE_FIELDS, LABELS, compare, freeze, prepare
from research.follow_up_oracle import validate_scenarios


def test_blind_annotation_disagreement_and_freeze(tmp_path):
    def source(name, ids):
        path = tmp_path / f"{name}.jsonl"
        path.write_text(
            "".join(
                json.dumps(
                    dict(
                        zip(
                            CASE_FIELDS,
                            (case, case, 1, f"synthetic response {case}", "fixture"),
                        )
                    )
                )
                + "\n"
                for case in ids
            ),
            encoding="utf-8",
        )
        return path

    def label(path, labels, *, adjudication=False):
        keys = ("case_id", *LABELS, *(("annotation_ref",) if adjudication else ()))
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(keys)
            for case, frequency in labels.items():
                writer.writerow(
                    (
                        case,
                        frequency,
                        "none",
                        "past_14_days",
                        *(("review-log-1",) if adjudication else ()),
                    )
                )

    dev, locked = source("dev", ("dev1", "dev2")), source("locked", ("eval1",))
    sheets = tmp_path / "sheets"
    prepare(dev, locked, sheets)
    for file in sheets.glob("*.csv"):
        with file.open(encoding="utf-8-sig", newline="") as stream:
            assert all(
                not row[field] for row in csv.DictReader(stream) for field in LABELS
            )
    dev_paths = tuple(sheets / f"dev-{name}.csv" for name in ("a", "b", "judged"))
    locked_paths = tuple(sheets / f"locked-{name}.csv" for name in ("a", "b", "judged"))
    label(dev_paths[0], {"dev1": 0, "dev2": 2})
    label(dev_paths[1], {"dev1": 0, "dev2": 2})
    label(dev_paths[2], {}, adjudication=True)
    label(locked_paths[0], {"eval1": 1})
    label(locked_paths[1], {"eval1": 2})
    audit = tmp_path / "audit"
    compare(locked, *locked_paths[:2], audit)
    assert "eval1,1,none,past_14_days,2" in (audit / "adjudicate.csv").read_text(
        encoding="utf-8-sig"
    )
    summary = json.loads((audit / "agreement.json").read_text(encoding="utf-8"))
    assert summary["gold_frequency"]["weighted_pairs"] == 1
    label(locked_paths[2], {}, adjudication=True)
    output = tmp_path / "final"
    with pytest.raises(ValueError, match="every expected"):
        freeze(
            dev, locked, [dev_paths, locked_paths], output, validation_groups=1, seed=42
        )
    assert not output.exists()
    label(locked_paths[2], {"eval1": 2}, adjudication=True)
    freeze(dev, locked, [dev_paths, locked_paths], output, validation_groups=1, seed=42)
    evaluation = output / "locked_evaluation.jsonl"
    assert (
        json.loads(evaluation.read_text(encoding="utf-8"))["annotation_ref"]
        == "review-log-1"
    )
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert (
        manifest["files"][evaluation.name]
        == hashlib.sha256(evaluation.read_bytes()).hexdigest()
    )
    with pytest.raises(FileExistsError):
        freeze(
            dev, locked, [dev_paths, locked_paths], output, validation_groups=1, seed=42
        )


def test_oracle_requires_a_complete_unique_branch_pair():
    scenario = {
        "case_id": "fixture",
        "author_ref": "test",
        "item_id": 1,
        "initial_answer": "有時",
        "system_clarification": "大概幾多日？",
        "gold_frequency": "unresolved",
        "branches": [
            {
                "turn": 1,
                "action_id": "clarify-reply",
                "outcome": "reply",
                "text": "有幾天",
            },
            {
                "turn": 1,
                "action_id": "clarify-refusal",
                "outcome": "refusal",
                "text": None,
            },
        ],
    }
    assert validate_scenarios([scenario]) == {"scenarios": 1, "branches": 2}
    with pytest.raises(ValueError, match="24–32"):
        validate_scenarios([scenario], formal=True)
    with pytest.raises(ValueError, match="duplicate Oracle branch"):
        validate_scenarios([scenario | {"branches": scenario["branches"] * 2}])
