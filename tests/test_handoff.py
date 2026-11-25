import csv
import json

import pytest


def test_followup_publish_refuses_blank_author_content_then_reuses_blind_ids(tmp_path):
    from research.pilot_package import build
    from research.handoff import publish_followups

    root = tmp_path / "package"
    build(root, git_sha="fixture")
    with pytest.raises(ValueError, match="author"):
        publish_followups(root, tmp_path / "blank")
    path = root / "private/followup_author_template.csv"
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fields, rows = reader.fieldnames, list(reader)
    for index, row in enumerate(rows):
        row.update(
            followup_response=f"過去14天有{index % 15}天。",
            author_ref="synthetic-test-only",
        )
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fields)
        writer.writeheader()
        writer.writerows(rows)
    publish_followups(root, tmp_path / "published")
    with (tmp_path / "published/followup_a.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        cases = list(csv.DictReader(file))
    assert len(cases) == 32 and all("待作者" not in row["text"] for row in cases)
    mapping = json.loads((root / "private/followup_mapping.json").read_text())
    assert {row["case_id"] for row in cases} == set(mapping)


def test_followup_freeze_inherits_parent_split_and_group(tmp_path):
    from research.handoff import freeze_followups

    # A separate synthetic two-case fixture, unrelated to human Dataset B labels.
    package = tmp_path / "package"
    (package / "private").mkdir(parents=True)
    parents = tmp_path / "parents"
    parents.mkdir()
    for split, key in (
        ("development_train", "a"),
        ("development_validation", "b"),
        ("locked_evaluation", "c"),
    ):
        (parents / f"{split}.jsonl").write_text(
            json.dumps(
                dict(
                    case_id=key,
                    group_id=f"g-{key}",
                    item_id=1,
                    text="過去兩週有幾天",
                    source_id="fixture",
                    gold_frequency=1,
                    ambiguity="none",
                    timeframe="past_14_days",
                    annotation_ref="fixture",
                )
            )
            + "\n",
            encoding="utf-8",
        )
    mapping = {
        f"q-{key}": dict(
            case_id=f"F-{key}",
            parent_id=key,
            split="locked" if key == "c" else "development",
        )
        for key in ("a", "b", "c")
    }
    (package / "private/followup_mapping.json").write_text(json.dumps(mapping))
    author = package / "private/followup_author_template.csv"
    with author.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, ("case_id", "parent_id", "item_id", "followup_response", "author_ref")
        )
        writer.writeheader()
        writer.writerows(
            dict(
                case_id=f"F-{key}",
                parent_id=key,
                item_id=1,
                followup_response=f"reply {key}",
                author_ref="fixture",
            )
            for key in ("a", "b", "c")
        )
    for name in ("a", "b", "adjudication"):
        with (tmp_path / f"{name}.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                (
                    "case_id",
                    "gold_frequency",
                    "ambiguity",
                    "timeframe",
                    "annotation_ref",
                    "item_id",
                    "question",
                    "text",
                ),
            )
            writer.writeheader()
            if name != "adjudication":
                writer.writerows(
                    dict(
                        case_id=blind,
                        gold_frequency="1",
                        ambiguity="none",
                        timeframe="past_14_days",
                        item_id=1,
                        question="fixture question",
                        text=f"reply {mapping[blind]['parent_id']}",
                    )
                    for blind in mapping
                )
    from research.handoff import _visible_hash
    import hashlib

    (package / "private/followup_issued_manifest.json").write_text(
        json.dumps(
            dict(
                author_source_sha256=hashlib.sha256(author.read_bytes()).hexdigest(),
                visible_hashes={
                    blind: _visible_hash(
                        dict(
                            case_id=blind,
                            item_id=1,
                            question="fixture question",
                            text=f"reply {entry['parent_id']}",
                        )
                    )
                    for blind, entry in mapping.items()
                },
            )
        )
    )
    freeze_followups(
        package,
        parents,
        tmp_path / "a.csv",
        tmp_path / "b.csv",
        tmp_path / "adjudication.csv",
        tmp_path / "frozen",
    )
    val = json.loads((tmp_path / "frozen/development_validation.jsonl").read_text())
    assert val["case_id"] == "F-b" and val["group_id"] == "g-b"
    from research.experiment_runner import run_e2

    config = dict(provider="rule", mode="synthetic")
    run_e2(
        parents / "development_validation.jsonl",
        tmp_path / "initial",
        turn="initial",
        metadata=config,
    )
    paired = dict(
        config,
        dataset_version="dataset-b-synthetic-pilot-v1",
        followup_manifest=str(tmp_path / "frozen/manifest.json"),
        parent_dir=str(parents),
        split_role="development_validation",
        initial_predictions=str(tmp_path / "initial/e2a_predictions.csv"),
        initial_manifest=str(tmp_path / "initial/experiment_manifest.json"),
    )
    run_e2(
        tmp_path / "frozen/development_validation.jsonl",
        tmp_path / "paired",
        turn="clarification",
        metadata=paired,
    )
    report = json.loads((tmp_path / "paired/paired_summary.json").read_text())
    assert report["pairs"] == 1 and report["both_resolvable"] == 1
    author.write_text(author.read_text() + "\n")
    with pytest.raises(ValueError, match="author source"):
        freeze_followups(
            package,
            parents,
            tmp_path / "a.csv",
            tmp_path / "b.csv",
            tmp_path / "adjudication.csv",
            tmp_path / "stale",
        )
