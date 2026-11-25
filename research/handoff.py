"""Publish human-written follow-ups and convert completed Oracle templates."""

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

from research.annotation import LABELS, _write_csv, _read_labels, _candidate
from research.dataset_b import read_cases, _validate_row
from research.follow_up_oracle import validate_scenarios


def _visible_hash(row):
    visible = {key: str(row[key]) for key in ("case_id", "item_id", "question", "text")}
    return hashlib.sha256(json.dumps(visible, sort_keys=True).encode()).hexdigest()


def publish_followups(package, output):
    author_file = package / "private/followup_author_template.csv"
    mapping = json.loads(
        (package / "private/followup_mapping.json").read_text(encoding="utf-8")
    )
    with author_file.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    by_id = {row["case_id"]: row for row in rows}
    if len(rows) != len(by_id) or set(by_id) != {
        row["case_id"] for row in mapping.values()
    }:
        raise ValueError("Author cases must exactly match the sealed mapping.")
    if any(
        not row["followup_response"].strip() or not row["author_ref"].strip()
        for row in rows
    ):
        raise ValueError(
            "Complete human author content and references before publishing."
        )
    visible = [
        dict(
            case_id=blind,
            item_id=by_id[entry["case_id"]]["item_id"],
            question=by_id[entry["case_id"]]["question"]
            + " "
            + by_id[entry["case_id"]]["clarification"],
            text=by_id[entry["case_id"]]["followup_response"],
        )
        for blind, entry in mapping.items()
    ]
    output.mkdir()
    for reviewer, seed in (("a", 1043), ("b", 1044)):
        order = list(visible)
        random.Random(seed).shuffle(order)
        _write_csv(output / f"followup_{reviewer}.csv", (*visible[0], *LABELS), order)
    (output / "manifest.json").write_text(
        json.dumps(
            dict(
                status="UNLABELLED_HUMAN_AUTHORED",
                author_source_sha256=hashlib.sha256(
                    author_file.read_bytes()
                ).hexdigest(),
                files={
                    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in output.glob("*.csv")
                },
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    issued = dict(
        author_source_sha256=hashlib.sha256(author_file.read_bytes()).hexdigest(),
        visible_hashes={row["case_id"]: _visible_hash(row) for row in visible},
    )
    (package / "private/followup_issued_manifest.json").write_text(
        json.dumps(issued, indent=2), encoding="utf-8"
    )
    (output / "blind_sources.jsonl").write_text(
        "".join(json.dumps(dict(case_id=key)) + "\n" for key in sorted(mapping)),
        encoding="utf-8",
    )


def freeze_followups(package, parent_dir, a_file, b_file, adjudication, output):
    if a_file.samefile(b_file):
        raise ValueError("Provide distinct blind annotation files.")
    mapping_path = package / "private/followup_mapping.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    expected = set(mapping)
    issued = json.loads(
        (package / "private/followup_issued_manifest.json").read_text(encoding="utf-8")
    )
    author_path = package / "private/followup_author_template.csv"
    if (
        hashlib.sha256(author_path.read_bytes()).hexdigest()
        != issued["author_source_sha256"]
    ):
        raise ValueError("Published author source has changed; reissue blind sheets.")
    for path in (a_file, b_file):
        with path.open(encoding="utf-8-sig", newline="") as file:
            visible_rows = list(csv.DictReader(file))
        if len(visible_rows) != len(expected) or any(
            _visible_hash(row) != issued["visible_hashes"].get(row["case_id"])
            for row in visible_rows
        ):
            raise ValueError(
                "Annotation visible content differs from the issued version."
            )
    (left, a_hash), (right, b_hash) = (
        _read_labels(path, expected) for path in (a_file, b_file)
    )
    conflicts = {key for key in expected if left[key][0] != right[key][0]}
    judged, adjudication_hash = _read_labels(adjudication, conflicts, adjudication=True)
    with (package / "private/followup_author_template.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        rows = list(csv.DictReader(file))
    authors = {row["case_id"]: row for row in rows}
    if len(authors) != len(rows) or set(authors) != {
        row["case_id"] for row in mapping.values()
    }:
        raise ValueError("Author IDs must match the frozen followup selection.")
    if any(
        not row["followup_response"].strip() or not row["author_ref"].strip()
        for row in rows
    ):
        raise ValueError("Missing human author content.")
    parents, parent_hashes = {}, {}
    for split in ("development_train", "development_validation", "locked_evaluation"):
        path = parent_dir / f"{split}.jsonl"
        parent_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        for row in read_cases(path):
            if row["case_id"] in parents:
                raise ValueError("Duplicate parent across frozen splits.")
            parents[row["case_id"]] = (split, row)
    splits = {
        key: []
        for key in ("development_train", "development_validation", "locked_evaluation")
    }
    links = {}
    for blind, entry in sorted(mapping.items()):
        split, parent = parents[entry["parent_id"]]
        authored = authors[entry["case_id"]]
        if (
            authored["parent_id"] != entry["parent_id"]
            or int(authored["item_id"]) != parent["item_id"]
        ):
            raise ValueError("Followup parent/item mismatch.")
        if (split == "locked_evaluation") != (entry["split"] == "locked"):
            raise ValueError("Followup split conflicts with sealed selection.")
        source = dict(
            case_id=entry["case_id"],
            group_id=parent["group_id"],
            item_id=parent["item_id"],
            text=authored["followup_response"],
            source_id=authored["author_ref"],
        )
        labels, reference = (
            judged[blind]
            if blind in conflicts
            else (left[blind][0], f"blind-a+b:{a_hash}:{b_hash}")
        )
        row = _candidate(source, labels, reference)
        _validate_row(row)
        splits[split].append(row)
        links[row["case_id"]] = dict(
            parent_id=entry["parent_id"], group_id=row["group_id"], split=split
        )
    output.mkdir()
    for split, rows in splits.items():
        (output / f"{split}.jsonl").write_text(
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                for row in rows
            ),
            encoding="utf-8",
        )
    (output / "paired_cases.json").write_text(
        json.dumps(links, indent=2), encoding="utf-8"
    )
    (output / "manifest.json").write_text(
        json.dumps(
            dict(
                parent_files=parent_hashes,
                annotations=dict(a=a_hash, b=b_hash, adjudication=adjudication_hash),
                files={
                    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in output.iterdir()
                    if path.is_file()
                },
            ),
            indent=2,
        ),
        encoding="utf-8",
    )


def convert_oracle(source, output):
    with source.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    scenarios = []
    for row in rows:
        if any(
            not row[key].strip()
            for key in (
                "author_ref",
                "initial_answer",
                "followup_response",
                "gold_frequency",
            )
        ):
            raise ValueError("Complete human Oracle content before conversion.")
        gold = row["gold_frequency"]
        gold = gold if gold == "unresolved" else int(gold)
        scenarios.append(
            dict(
                case_id=row["case_id"],
                item_id=int(row["item_id"]),
                author_ref=row["author_ref"],
                initial_answer=row["initial_answer"],
                system_clarification=row["clarification"],
                gold_frequency=gold,
                branches=[
                    dict(
                        turn=1,
                        action_id="clarify-reply",
                        outcome="reply",
                        text=row["followup_response"],
                    ),
                    dict(
                        turn=1,
                        action_id="clarify-unresolved",
                        outcome="unresolved",
                        text=None,
                    ),
                    dict(
                        turn=1,
                        action_id="clarify-refusal",
                        outcome="refusal",
                        text=None,
                    ),
                ],
            )
        )
    validate_scenarios(scenarios, formal=True)
    with output.open("x", encoding="utf-8") as file:
        json.dump(scenarios, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=("followups", "oracle", "freeze-followups")
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--parent-dir", type=Path)
    parser.add_argument("--a", type=Path)
    parser.add_argument("--b", type=Path)
    parser.add_argument("--adjudication", type=Path)
    args = parser.parse_args()
    if args.operation == "followups":
        publish_followups(args.source, args.output)
    elif args.operation == "oracle":
        convert_oracle(args.source, args.output)
    else:
        if not all((args.parent_dir, args.a, args.b, args.adjudication)):
            parser.error(
                "Followup freeze requires parent dir, A/B sheets and adjudication."
            )
        freeze_followups(
            args.source, args.parent_dir, args.a, args.b, args.adjudication, args.output
        )
