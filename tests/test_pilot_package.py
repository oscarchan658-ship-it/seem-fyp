import csv
import json


def test_pilot_has_96_unlabelled_blind_cases_and_oracle_templates(tmp_path):
    from research.pilot_package import build

    build(tmp_path / "package", git_sha="test-sha")
    root = tmp_path / "package"
    source = [
        json.loads(line)
        for line in (root / "private/source_cases.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(source) == 96
    assert {row["item_id"] for row in source} == set(range(1, 9))
    assert all("gold_frequency" not in row for row in source)
    mapping = json.loads((root / "private/blind_mapping.json").read_text())
    assert len(mapping) == 96
    for reviewer in ("a", "b"):
        with (root / f"annotator_{reviewer}.csv").open(
            encoding="utf-8-sig", newline=""
        ) as file:
            rows = list(csv.DictReader(file))
        assert len(rows) == len({row["case_id"] for row in rows}) == 96
        assert {row["case_id"] for row in rows} == set(mapping)
        assert all(
            row["gold_frequency"] == row["ambiguity"] == row["timeframe"] == ""
            for row in rows
        )
        assert set(rows[0]) == {
            "case_id",
            "item_id",
            "question",
            "text",
            "gold_frequency",
            "ambiguity",
            "timeframe",
        }
        assert all(
            not any(
                word in str(row).lower()
                for word in ("locked", "development", "source_id", "group_id")
            )
            for row in rows
        )
    for reviewer in ("a", "b"):
        with (root / f"followup_{reviewer}.csv").open(
            encoding="utf-8-sig", newline=""
        ) as file:
            assert len(list(csv.DictReader(file))) == 32
    with (root / "oracle/oracle_template.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        scenarios = list(csv.DictReader(file))
    assert len(scenarios) == 24 and all(
        row["gold_frequency"] == "" for row in scenarios
    )
    with (root / "private/coverage_matrix.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        coverage = list(csv.DictReader(file))
    assert len({row["category"] for row in coverage}) == 12
    assert sum(row["split"] == "development" for row in coverage) == 64
    assert sum(row["split"] == "locked" for row in coverage) == 32


def test_blind_restore_is_complete_and_rejects_reused_file(tmp_path):
    from research.pilot_package import build
    from research.blind_annotation import restore

    root = tmp_path / "package"
    build(root, git_sha="test")
    sheets = []
    for reviewer in ("a", "b"):
        path = root / f"annotator_{reviewer}.csv"
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            fields, rows = reader.fieldnames, list(reader)
        for row in rows:
            row.update(
                gold_frequency="unresolved", ambiguity="uncertain", timeframe="unclear"
            )
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fields)
            writer.writeheader()
            writer.writerows(rows)
        sheets.append(path)
    output = tmp_path / "restored"
    restore(root / "private/blind_mapping.json", *sheets, output)
    for split, count in (("development", 64), ("locked", 32)):
        with (output / f"{split}-a.csv").open(encoding="utf-8-sig") as file:
            assert len(list(csv.DictReader(file))) == count
    import pytest

    with pytest.raises(ValueError, match="distinct"):
        restore(
            root / "private/blind_mapping.json", sheets[0], sheets[0], tmp_path / "bad"
        )
