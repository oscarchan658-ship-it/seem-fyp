import pytest


def test_coverage_split_is_grouped_order_independent_and_covers_repeated_strata():
    from research.coverage_split import split_coverage

    rows, categories = [], {}
    for item in range(1, 9):
        for variant in range(4):
            key = f"{item}-{variant}"
            rows.append(
                dict(
                    case_id=key, group_id=key, item_id=item, gold_frequency=variant % 2
                )
            )
            categories[key] = f"category-{variant % 2}"
    first = split_coverage(rows, categories, seed=42)
    assert first == split_coverage(rows[::-1], categories, seed=42)
    train, validation, report = first
    assert {row["group_id"] for row in train}.isdisjoint(
        row["group_id"] for row in validation
    )
    assert (
        {row["item_id"] for row in train}
        == {row["item_id"] for row in validation}
        == set(range(1, 9))
    )
    assert report["status"] == "READY"
    assert len(validation) == 8


def test_e2_fixed_denominators_and_abstain_is_not_zero():
    from research.e2 import metrics

    rows = [
        dict(gold_frequency=0, prediction=0, error=None),
        dict(gold_frequency=1, prediction=None, error="timeout"),
        dict(gold_frequency=2, prediction=1, error=None),
        dict(gold_frequency="unresolved", prediction=1, error=None),
    ]
    summary = metrics(rows)
    assert summary["frequency_accuracy"] == 1 / 3
    assert summary["macro_f1"] == 0.25
    assert summary["abstention_rate"] == 0.25
    assert summary["unresolved_false_accept_rate"] == 1
    assert summary["selective_risk"] == pytest.approx(2 / 3)
    assert summary["class_support"] == [1, 1, 1, 0]
    assert metrics([])["macro_f1"] is None
    assert (
        metrics([dict(gold_frequency=0, prediction=None, error=None)])["selective_risk"]
        is None
    )


def test_validation_threshold_uses_p1_risk_and_excludes_unresolved_accepts():
    from research.e2 import freeze_threshold

    rows = [
        dict(gold_frequency=0, prediction=0, confidence=0.9),
        dict(gold_frequency="unresolved", prediction=1, confidence=0.1),
        dict(gold_frequency=1, prediction=None, confidence=0.99),
    ]
    result = freeze_threshold(rows)
    assert result["baseline_risk"] == 0.5
    assert result["baseline_accepted"] == 2
    assert result["threshold"] == 0.1
    assert result["status"] == "FROZEN"
    assert (
        freeze_threshold([dict(gold_frequency=0, prediction=None, confidence=None)])[
            "status"
        ]
        == "NOT RUN"
    )


def test_r1_frozen_policy_preserves_local_interval_evidence():
    from nlu_provider import ClarificationContext, NluRequest, RuleProvider
    from research.policy_simulator import FrozenPrediction, ScriptedReply, simulate

    payload = RuleProvider().predict(
        NluRequest(
            1,
            "1 day",
            clarification=ClarificationContext(1, "frequency_in_past_14_days"),
        )
    )
    frozen = FrozenPrediction("rule", payload)
    replay = simulate(
        "r1",
        1,
        frozen,
        0,
        "P1",
        {(1, "confirm-batch"): ScriptedReply("reply", confirmed_value=0)},
    )
    assert replay.confirmed == 0


def test_threshold_input_requires_initial_turn_and_frozen_validation_hash(tmp_path):
    import hashlib
    import json
    from research.experiment_runner import validate_threshold_input

    cases = tmp_path / "validation.jsonl"
    cases.write_text("{}\n")
    manifest = tmp_path / "manifest.json"
    digest = hashlib.sha256(cases.read_bytes()).hexdigest()
    manifest.write_text(
        json.dumps(
            dict(
                files={
                    "development_validation.jsonl": digest,
                    "locked_evaluation.jsonl": "other",
                }
            )
        )
    )
    config = dict(dataset_manifest=str(manifest), split_role="development_validation")
    validate_threshold_input(cases, config, "initial")
    with pytest.raises(ValueError, match="initial"):
        validate_threshold_input(cases, config, "clarification")
    cases.write_text("changed")
    with pytest.raises(ValueError, match="hash"):
        validate_threshold_input(cases, config, "initial")
