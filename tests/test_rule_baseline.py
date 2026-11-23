from research.rule_baseline import run


def test_c12_rule_pilot_reports_abstention_separately():
    predictions, summary = run(
        [
            {
                "case_id": "exact",
                "item_id": 1,
                "text": "過去兩週有幾天",
                "gold_frequency": 1,
            },
            {
                "case_id": "abstain",
                "item_id": 1,
                "text": "沒說時間",
                "gold_frequency": 0,
            },
            {
                "case_id": "ambiguous",
                "item_id": 1,
                "text": "過去兩週有時",
                "gold_frequency": "unresolved",
            },
        ]
    )
    assert [row["outcome"] for row in predictions] == [
        "correct",
        "abstained",
        "unresolved",
    ]
    assert [row["prediction"] for row in predictions] == [1, None, None]
    assert all(row["runtime_ms"] >= 0 and "text" not in row for row in predictions)
    assert summary == {
        "total": 3,
        "accepted": 1,
        "abstained": 2,
        "resolved_gold": 2,
        "accepted_resolved": 1,
        "coverage": 1 / 3,
        "accepted_resolved_accuracy": 1,
    }
