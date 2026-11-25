"""Restore sealed split IDs after two independent blind sheets are returned."""

import argparse
import json
from pathlib import Path

from research.annotation import LABELS, _read_labels, _write_csv


def restore(mapping_file, a_file, b_file, output):
    if a_file.samefile(b_file):
        raise ValueError("Provide two distinct annotation sheets.")
    mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
    expected = set(mapping)
    labels = [_read_labels(path, expected) for path in (a_file, b_file)]
    output.mkdir()
    for reviewer, (entries, _) in zip(("a", "b"), labels):
        for split in ("development", "locked"):
            rows = [
                dict(
                    zip(
                        ("case_id", *LABELS),
                        (mapping[key]["case_id"], *entries[key][0]),
                    )
                )
                for key in sorted(expected)
                if mapping[key]["split"] == split
            ]
            _write_csv(output / f"{split}-{reviewer}.csv", ("case_id", *LABELS), rows)
    (output / "provenance.json").write_text(
        json.dumps(
            {
                "blind_annotation_hashes": dict(
                    zip(("a", "b"), (entry[1] for entry in labels))
                ),
                "mapping_sha256": __import__("hashlib")
                .sha256(mapping_file.read_bytes())
                .hexdigest(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for field in ("mapping", "a", "b", "output"):
        cli.add_argument(field, type=Path)
    args = cli.parse_args()
    restore(args.mapping, args.a, args.b, args.output)
