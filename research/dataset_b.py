"""Validate independently collected Dataset B sets and produce a freeze manifest."""

import argparse
import hashlib
import json
import random
import unicodedata
from pathlib import Path


_REQUIRED = {
    "case_id",
    "group_id",
    "item_id",
    "text",
    "gold_frequency",
    "ambiguity",
    "timeframe",
    "source_id",
    "annotation_ref",
}
_TIMEFRAMES = {"past_14_days", "missing", "other", "unclear"}
_AMBIGUITIES = {
    "none",
    "ambiguous_frequency",
    "uncertain",
    "contradiction",
    "off_topic",
}


def _validate_row(row):
    if not isinstance(row, dict) or row.keys() != _REQUIRED:
        raise ValueError("Unexpected or missing Dataset B fields.")
    for field in ("case_id", "group_id", "text", "source_id", "annotation_ref"):
        if type(row[field]) is not str or not row[field].strip():
            raise ValueError(f"Invalid {field}.")
        if field != "text" and row[field] != row[field].strip():
            raise ValueError(f"Invalid whitespace in {field}.")
    item_id = row["item_id"]
    if type(item_id) is not int or not 1 <= item_id <= 8:
        raise ValueError("Invalid item_id.")
    gold = row["gold_frequency"]
    if gold != "unresolved" and (type(gold) is not int or not 0 <= gold <= 3):
        raise ValueError("Invalid gold_frequency.")
    for field, labels in (("timeframe", _TIMEFRAMES), ("ambiguity", _AMBIGUITIES)):
        if type(row[field]) is not str or row[field] not in labels:
            raise ValueError(f"Invalid {field}.")


def _fingerprint(text):
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return "".join(char for char in normalized if char.isalnum())


def _manifest(rows):
    stable = json.dumps(
        sorted(rows, key=lambda row: row["case_id"]),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return {
        "count": len(rows),
        "sha256": hashlib.sha256(stable.encode("utf-8")).hexdigest(),
    }


def validate_sets(development, locked_evaluation):
    """Check provenance fields and prevent group or exact reply leakage across sets."""
    case_ids = set()
    replies = set()
    groups = {}
    manifest = {}
    for collection, rows in (
        ("development", development),
        ("locked_evaluation", locked_evaluation),
    ):
        if not rows:
            raise ValueError(f"Empty {collection} set.")
        for row in rows:
            _validate_row(row)
            case_id, group = row["case_id"], row["group_id"]
            if case_id in case_ids:
                raise ValueError(f"duplicate case_id: {case_id}")
            if groups.setdefault(group, collection) != collection:
                raise ValueError(f"group crosses sets: {group}")
            key = (row["item_id"], _fingerprint(row["text"]))
            if not key[1] or key in replies:
                raise ValueError(f"empty or duplicate reply: {case_id}")
            case_ids.add(case_id)
            replies.add(key)
        manifest[collection] = _manifest(rows)
    return manifest


def split_development(rows, *, validation_groups, seed):
    """Return stable train and validation rows from the development set only."""
    groups = sorted({row["group_id"] for row in rows})
    if not 0 < validation_groups < len(groups):
        raise ValueError("Train and validation both need at least one group.")
    random.Random(seed).shuffle(groups)
    validation_set = set(groups[:validation_groups])
    ordered = sorted(rows, key=lambda row: row["case_id"])
    return (
        [row for row in ordered if row["group_id"] not in validation_set],
        [row for row in ordered if row["group_id"] in validation_set],
    )


def read_cases(path):
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development", type=Path)
    parser.add_argument("locked_evaluation", type=Path)
    args = parser.parse_args()

    print(
        json.dumps(
            validate_sets(
                read_cases(args.development), read_cases(args.locked_evaluation)
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
