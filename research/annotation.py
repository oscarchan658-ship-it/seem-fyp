"""Prepare blind Dataset B workbooks, compare ratings and freeze adjudicated labels."""

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from research.dataset_b import read_cases, split_development, validate_sets
from research.statistics import cohens_kappa

CASE_FIELDS = ("case_id", "group_id", "item_id", "text", "source_id")
LABELS = ("gold_frequency", "ambiguity", "timeframe")
FREQUENCIES = ("0", "1", "2", "3", "unresolved")
AMBIGUITIES = ("none", "ambiguous_frequency", "uncertain", "contradiction", "off_topic")
TIMEFRAMES = ("past_14_days", "missing", "other", "unclear")
VOCABULARY = (FREQUENCIES, AMBIGUITIES, TIMEFRAMES)


def _write_csv(path, fields, rows):
    with path.open("x", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _candidate(row, labels, reference):
    frequency, ambiguity, timeframe = labels
    # Excel quoting never changes the labels imported from completed sheets.
    frequency = int(frequency) if frequency in FREQUENCIES[:4] else frequency
    return {
        **row,
        "gold_frequency": frequency,
        "ambiguity": ambiguity,
        "timeframe": timeframe,
        "annotation_ref": reference,
    }


def _sources(dev_file, locked_file):
    sets = read_cases(dev_file), read_cases(locked_file)
    for rows in sets:
        if any(
            not isinstance(row, dict) or row.keys() != set(CASE_FIELDS) for row in rows
        ):
            raise ValueError("Source records must contain only the five case fields.")
        if any(
            isinstance(row["case_id"], str)
            and row["case_id"].lstrip().startswith(("=", "+", "-", "@"))
            for row in rows
        ):
            raise ValueError("Case IDs must be safe to read in a spreadsheet.")
    # Validate the case metadata and leakage before distributing sheets.
    validate_sets(
        *(
            [
                _candidate(row, ("unresolved", "uncertain", "unclear"), "unlabelled")
                for row in rows
            ]
            for rows in sets
        )
    )
    return sets


def prepare(dev_file, locked_file, output):
    sets = _sources(dev_file, locked_file)
    output.mkdir()
    for name, rows in zip(("development", "locked"), sets):
        # Protect spreadsheet users from formula cells while keeping the original JSONL intact.
        safe = [
            {
                key: "'" + value
                if isinstance(value, str)
                and value.lstrip().startswith(("=", "+", "-", "@"))
                else value
                for key, value in row.items()
            }
            for row in rows
        ]
        for reviewer in ("a", "b"):
            _write_csv(output / f"{name}-{reviewer}.csv", (*CASE_FIELDS, *LABELS), safe)


def _read_labels(path, expected, *, adjudication=False):
    content = path.read_bytes()
    result = {}
    with io.StringIO(content.decode("utf-8-sig"), newline="") as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames or []
        required = {"case_id", *LABELS}
        if adjudication:
            required.add("annotation_ref")
        if not required.issubset(fields) or len(fields) != len(set(fields)):
            raise ValueError(f"Missing or duplicate annotation columns in {path.name}.")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(
                    f"Invalid annotation row at {path.name}:{reader.line_num}."
                )
            case = row["case_id"]
            if case.lstrip().startswith(("=", "+", "-", "@")):
                raise ValueError("Case IDs must be safe to read in a spreadsheet.")
            if case not in expected or case in result:
                raise ValueError("Unknown or duplicate case ID.")
            values = tuple(row[key] for key in LABELS)
            if any(value not in allowed for value, allowed in zip(values, VOCABULARY)):
                raise ValueError(f"Missing or invalid label for {case}.")
            ref = row.get("annotation_ref", "")
            if adjudication and not ref.strip():
                raise ValueError(f"Missing adjudication reference for {case}.")
            result[case] = (values, ref)
    if result.keys() != expected:
        raise ValueError(
            "Annotation sheets must cover every expected case exactly once."
        )
    return result, hashlib.sha256(content).hexdigest()


def agreement(left, right):
    cases = sorted(left)
    if not cases or left.keys() != right.keys():
        raise ValueError("Agreement requires identical nonempty case sets.")
    result = {}
    for index, field in enumerate(LABELS):
        a = [left[case][0][index] for case in cases]
        b = [right[case][0][index] for case in cases]
        result[field] = {
            "kappa": cohens_kappa(a, b, VOCABULARY[index]),
            "matrix": [
                {"a": x, "b": y, "count": count}
                for (x, y), count in sorted(Counter(zip(a, b)).items())
            ],
        }
        if index == 0:
            resolved = [(x, y) for x, y in zip(a, b) if "unresolved" not in (x, y)]
            result[field]["weighted_pairs"] = len(resolved)
            result[field]["weighted_kappa"] = (
                cohens_kappa(*map(list, zip(*resolved)), FREQUENCIES[:4], ordered=True)
                if resolved
                else None
            )
    return result


def compare(source, a_file, b_file, output):
    if a_file.samefile(b_file):
        raise ValueError("Provide two distinct annotation sheets.")
    expected = {row["case_id"] for row in read_cases(source)}
    (left, _), (right, _) = (_read_labels(path, expected) for path in (a_file, b_file))
    output.mkdir()
    disagreements = [
        case for case in sorted(expected) if left[case][0] != right[case][0]
    ]
    fields = (
        "case_id",
        *(f"{side}_{label}" for side in ("a", "b") for label in LABELS),
        *LABELS,
        "annotation_ref",
    )
    _write_csv(
        output / "adjudicate.csv",
        fields,
        (
            dict(zip(fields, (case, *left[case][0], *right[case][0])))
            for case in disagreements
        ),
    )
    (output / "agreement.json").write_text(
        json.dumps(agreement(left, right), indent=2), encoding="utf-8"
    )


def freeze(
    dev_file,
    locked_file,
    reviewers,
    output,
    *,
    validation_groups=None,
    seed=42,
    categories=None,
):
    sets = _sources(dev_file, locked_file)
    final = []
    provenance = {}
    for name, rows, paths in zip(
        ("development", "locked"), sets, reviewers, strict=True
    ):
        if paths[0].samefile(paths[1]):
            raise ValueError("Provide two distinct annotation sheets.")
        expected = {row["case_id"] for row in rows}
        (left, a_hash), (right, b_hash) = (
            _read_labels(path, expected) for path in paths[:2]
        )
        conflicts = {case for case in expected if left[case][0] != right[case][0]}
        adjudicated, adjudication_hash = _read_labels(
            paths[2], conflicts, adjudication=True
        )
        hashes = (a_hash, b_hash, adjudication_hash)
        provenance[name] = dict(
            zip(("annotator_a", "annotator_b", "adjudication"), hashes)
        )
        final.append(
            [
                _candidate(row, *adjudicated[row["case_id"]])
                if row["case_id"] in conflicts
                else _candidate(
                    row,
                    left[row["case_id"]][0],
                    f"{name}:a+b:{row['case_id']}:{hashes[0][:12]}:{hashes[1][:12]}",
                )
                for row in rows
            ]
        )
    manifest = validate_sets(*final)
    coverage = None
    if categories is not None:
        from research.coverage_split import split_coverage

        train, validation, coverage = split_coverage(final[0], categories, seed=seed)
        if coverage["status"] != "READY":
            raise ValueError("SPLIT_REVIEW_REQUIRED: inspect Development coverage.")
    else:
        train, validation = split_development(
            final[0], validation_groups=validation_groups, seed=seed
        )
    output.mkdir()
    splits = {
        "development_train": train,
        "development_validation": validation,
        "locked_evaluation": final[1],
    }
    manifest.update(
        {
            "seed": seed,
            "validation_groups": validation_groups,
            "coverage": coverage,
            "provenance": provenance,
            "files": {},
        }
    )
    for name, rows in splits.items():
        data = "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in sorted(rows, key=lambda row: row["case_id"])
        ).encode("utf-8")
        (output / f"{name}.jsonl").write_bytes(data)
        manifest["files"][f"{name}.jsonl"] = hashlib.sha256(data).hexdigest()
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    stages = cli.add_subparsers(dest="stage", required=True)
    for name, fields in (
        ("prepare", ("development", "locked", "output")),
        ("compare", ("source", "a", "b", "output")),
        (
            "freeze",
            (
                "development",
                "locked",
                "dev_a",
                "dev_b",
                "dev_adjudication",
                "locked_a",
                "locked_b",
                "locked_adjudication",
                "output",
            ),
        ),
    ):
        stage = stages.add_parser(name)
        for field in fields:
            stage.add_argument(field, type=Path)
        if name == "freeze":
            choices = stage.add_mutually_exclusive_group(required=True)
            choices.add_argument("--validation-groups", type=int)
            choices.add_argument("--coverage-matrix", type=Path)
            stage.add_argument("--seed", type=int, required=True)
    args = cli.parse_args()
    if args.stage == "prepare":
        prepare(args.development, args.locked, args.output)
    elif args.stage == "compare":
        compare(args.source, args.a, args.b, args.output)
    else:
        categories = None
        if args.coverage_matrix:
            with args.coverage_matrix.open(encoding="utf-8-sig", newline="") as stream:
                matrix = list(csv.DictReader(stream))
            categories = {
                row["case_id"]: row["category"]
                for row in matrix
                if row["split"] == "development"
            }
        freeze(
            args.development,
            args.locked,
            [
                (args.dev_a, args.dev_b, args.dev_adjudication),
                (args.locked_a, args.locked_b, args.locked_adjudication),
            ],
            args.output,
            validation_groups=args.validation_groups,
            seed=args.seed,
            categories=categories,
        )


if __name__ == "__main__":
    main()
