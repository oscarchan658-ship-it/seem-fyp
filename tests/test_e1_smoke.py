import pytest

from research.e1_smoke import evaluate_smoke, run_smoke


def test_c17_smoke_reports_pipeline_checks_only():
    result = run_smoke()
    assert result == {
        "mode": "Engineering Smoke Test",
        "arms_checked": ["S", "N", "F"],
        "cases_checked_per_arm": 4,
        "empirical_e1": "NOT RUN",
    }


def test_c17_all_arms_require_exact_same_case_ids():
    gold = {"a": 0, "b": 1}
    complete = {"a": 0.0, "b": 0.8}
    with pytest.raises(ValueError, match="same test case IDs"):
        evaluate_smoke(gold, {"S": complete, "N": complete, "F": {"a": 0.7}})


def test_c17_confusion_and_tie_handling():
    gold = {"a": 0, "b": 1}
    tied = {"a": 0.5, "b": 0.5}
    results = evaluate_smoke(gold, {"S": tied, "N": tied, "F": tied})
    assert results["S"]["confusion"] == [[0, 1], [0, 1]]
    assert results["S"]["auroc"] == 0.5
    assert results["S"]["recall"] == 1
    assert results["S"]["macro_f1"] == pytest.approx(1 / 3)
