import pytest

from research.dataset_b import split_development, validate_sets


def case(case_id, group_id, text, *, gold=1):
    return {
        "case_id": case_id,
        "group_id": group_id,
        "item_id": 1,
        "text": text,
        "gold_frequency": gold,
        "ambiguity": "none",
        "timeframe": "past_14_days",
        "source_id": "synthetic-test",
        "annotation_ref": "fixture-only",
    }


def test_c11_keeps_groups_together_and_freezes_order_independent_manifest():
    development = [
        case("d1", "g1", "回答 1"),
        case("d2", "g1", "回答改寫"),
        case("d3", "g2", "回答 2"),
    ]
    evaluation = [case("e1", "g3", "獨立虛構案例", gold="unresolved")]
    assert validate_sets(development, evaluation) == validate_sets(
        development[::-1], evaluation
    )
    train, validation = split_development(development, validation_groups=1, seed=42)
    assert len(train) + len(validation) == 3
    assert {r["group_id"] for r in train}.isdisjoint(r["group_id"] for r in validation)
    assert split_development(development[::-1], validation_groups=1, seed=42) == (
        train,
        validation,
    )
    edited = [dict(evaluation[0], text="已修訂合成材料")]
    assert (
        validate_sets(development, evaluation)["locked_evaluation"]["sha256"]
        != (validate_sets(development, edited)["locked_evaluation"]["sha256"])
    )


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"case_id": "d1"}, "duplicate case_id"),
        ({"group_id": "g1"}, "group crosses"),
        ({"group_id": "g1 "}, "group_id"),
        ({"text": "有幾天  。"}, "duplicate reply"),
        ({"gold_frequency": False}, "gold_frequency"),
        ({"item_id": 9}, "item_id"),
        ({"timeframe": "guess"}, "timeframe"),
        ({"annotation_ref": ""}, "annotation_ref"),
    ],
)
def test_c11_rejects_leakage_and_invalid_labels(change, reason):
    dev = [case("d1", "g1", "有幾天")]
    locked = [case("e1", "g2", "沒有症狀") | change]
    with pytest.raises(ValueError, match=reason):
        validate_sets(dev, locked)
