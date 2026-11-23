import json
from unittest.mock import Mock

import pytest

from controller import decide_candidate, dispatch, new_session
from rule_nlu import extract
from schemas import Event, validate_nlu


@pytest.mark.parametrize(("text", "value"), [
    ("過去兩週有幾天出現此症狀", 1),
    ("過去兩週超過一半的日子", 2),
    ("過去兩週幾乎每天", 3),
    ("過去兩週完全沒有此症狀", 0),
])
def test_t09_t13_explicit_current_item_frequencies(text, value):
    out = validate_nlu(extract(1, text), 1)
    assert decide_candidate(out) == value


@pytest.mark.parametrize(("text", "ambiguity"), [
    ("上週有幾天", "uncertain"),
    ("有幾天", "uncertain"),
    ("完全沒有此症狀", "uncertain"),
    ("過去兩週有時", "ambiguous_frequency"),
    ("我不確定", "uncertain"),
    ("過去兩週並非完全沒有此症狀", "uncertain"),
    ("過去兩週幾乎每天睡不好", "off_topic"),
    ("過去兩週完全沒有，但也說幾乎每天", "contradiction"),
])
def test_t10_to_t16_abstains_on_unreliable_evidence(text, ambiguity):
    result = validate_nlu(extract(1, text), 1)
    assert result["ambiguity"] == ambiguity
    assert result["frequency_candidate"] is None and decide_candidate(result) is None


def test_t16_high_confidence_does_not_override_conflict():
    result = extract(1, "過去兩週完全沒有，但也說幾乎每天")
    result.update(frequency_candidate=3, symptom_present=True, confidence_signal=1)
    assert decide_candidate(validate_nlu(result, 1)) is None


@pytest.mark.parametrize("value", [0, None])
def test_t27_json_roundtrip_distinguishes_zero_and_null(value):
    result = extract(1, "過去兩週完全沒有")
    result["frequency_candidate"] = value
    assert validate_nlu(json.loads(json.dumps(result)), 1)["frequency_candidate"] is value


@pytest.mark.parametrize("changes", [
    {"item_id": 2}, {"extra": 0}, {"frequency_candidate": True},
    {"frequency_candidate": "0"}, {"frequency_candidate": 0.0},
    {"confidence_signal": float("inf")}, {"confidence_signal": float("nan")},
    {"model_version": None},
])
def test_t27_invalid_schema_cannot_write_answer(changes):
    state = new_session()
    for kind in ("START", "ACCEPT"):
        state = dispatch(state, Event(kind, state.session_id, state.revision)).state
    invalid = {**extract(1, "過去兩週完全沒有"), **changes}
    with pytest.raises(ValueError):
        validate_nlu(invalid, 1)
    text = Event("TEXT", state.session_id, state.revision, item_id=1, text="synthetic")
    out = dispatch(state, text, nlu=Mock(return_value=invalid))
    assert out.response_code == "nlu_unavailable" and not out.state.provisional_answers


def test_t27_requires_all_mandatory_keys():
    result = extract(1, "過去兩週完全沒有")
    del result["timeframe"]
    with pytest.raises(ValueError):
        validate_nlu(result, 1)
