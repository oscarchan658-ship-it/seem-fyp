import pytest

from research.evaluation import (
    observed_aurc,
    pareto_front,
    risk_coverage,
    select_threshold,
)
from research.policy_simulator import (
    FrozenPrediction,
    ScriptedReply,
    replay_questionnaire,
    simulate,
)
from rule_nlu import extract


def prediction(text, confidence=None):
    return FrozenPrediction(
        "fixture", extract(1, text) | {"confidence_signal": confidence}
    )


def test_c09_comparison_and_offline_confirmation():
    initial = prediction("過去兩週有幾天", 0.7)
    args = ("case", 1, initial, 2)
    oracle = {
        (1, "clarify-frequency"): ScriptedReply(
            "reply", prediction("過去兩週幾乎每天", 0.9)
        ),
        (1, "confirm-batch"): ScriptedReply("reply", confirmed_value=2),
        (2, "confirm-batch"): ScriptedReply("reply", confirmed_value=2),
        (2, "confirm-item"): ScriptedReply("reply", confirmed_value=2),
    }
    assert simulate(*args, "P0", {}).confirmed is None
    conservative = simulate(*args, "P1", oracle)
    batch = simulate(*args, "P2", oracle, threshold=0.8)
    item = simulate(*args, "P3", oracle, threshold=0.8)
    assert conservative.clarifications == 0
    assert batch.clarifications == item.clarifications == 1
    assert batch.trace[0] == item.trace[0]
    assert batch.trace[-1].action_id == "confirm-batch"
    assert item.trace[-1].action_id == "confirm-item"
    assert batch.confirmed == item.confirmed == 2 and batch.error == 0


def test_c19_missing_oracle_and_uncertainty_are_explicit():
    first = prediction("過去兩週有幾天")
    missing = simulate("case", 1, first, 1, "P2", {}, threshold=0.8)
    assert missing.outcome == "missing_branch" and missing.confirmed is None
    conflict = prediction("過去兩週完全沒有，但也說幾乎每天", 1.0)
    result = simulate(
        "case", 1, conflict, 1, "P2", {}, threshold=0.8, max_clarifications=0
    )
    assert result.outcome == "budget_exhausted" and result.reason == "contradiction"
    assert simulate("case", 1, first, 1, "P1", {}).outcome == "missing_branch"
    exact = simulate(
        "case",
        1,
        prediction("過去兩週有幾天", 0.8),
        1,
        "P2",
        {(1, "confirm-batch"): ScriptedReply("unresolved")},
        threshold=0.8,
    )
    assert exact.clarifications == 0 and exact.outcome == "unresolved"


def test_c20_risk_is_undefined_when_all_rows_are_rejected():
    records = [(0.8, True, True), (0.5, False, True), (1.0, False, False)]
    curve = risk_coverage(records, [1, 0.8, 0.5])
    assert curve[0].risk is None
    assert curve[1].coverage == pytest.approx(1 / 3)
    assert curve[2].risk == 0.5
    assert select_threshold(curve, baseline_risk=0).threshold == 0.8
    assert observed_aurc(curve) == pytest.approx((1 / 12, 1 / 3, 2 / 3))


def test_c26_pareto_retains_ties_and_excludes_missing_metrics():
    rows = {
        "a": (0.8, 0.1, 2, 1, 1),
        "tie": (0.8, 0.1, 2, 1, 1),
        "worse": (0.7, 0.2, 3, 2, 2),
        "fast": (0.7, 0.1, 1, 1, 1),
        "unknown": (0.99, None, 1, 1, 1),
    }
    assert pareto_front(rows) == (["a", "fast", "tie"], ["unknown"])


def test_c19_batch_and_item_confirmation_use_distinct_action_counts():
    items = {
        item: (
            f"case-{item}",
            FrozenPrediction(
                "fixture", extract(item, "過去兩週有幾天") | {"confidence_signal": 0.8}
            ),
            2,
            {(1, "confirm-item"): ScriptedReply("reply", confirmed_value=2)},
        )
        for item in range(1, 9)
    }
    batch_reply = {item: 2 for item in items}
    assert replay_questionnaire(items, "P2", threshold=0.8)[2] is None
    assert (
        replay_questionnaire(items, "P2", threshold=0.8, batch_reply={1: 2})[2] is None
    )
    batch = replay_questionnaire(items, "P2", threshold=0.8, batch_reply=batch_reply)
    item = replay_questionnaire(items, "P3", threshold=0.8)
    assert batch[2].total == item[2].total == 16
    assert batch[3:] == (1, 0) and item[3:] == (8, 0)
