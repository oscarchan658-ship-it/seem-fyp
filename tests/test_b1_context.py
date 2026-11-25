from unittest.mock import Mock

import pytest

from controller import dispatch, new_session
from evidence_manager import evaluate_candidate
from rule_nlu import extract
from schemas import Event


def send(state, kind, **payload):
    return dispatch(state, Event(kind, state.session_id, state.revision, **payload))


def test_c06_context_maps_approved_days_only_after_clarification():
    state = send(send(new_session(), "START").state, "ACCEPT").state
    state = send(state, "SELECT", item_id=1, value=0).state
    state = send(state, "SELECT", item_id=2, value=0).state
    state = send(
        state, "TEXT", item_id=3, text="I haven't slept well since last Monday"
    ).state
    assert state.clarification_item_id == 3
    out = send(state, "TEXT", item_id=3, text="Around five days")
    assert out.response_code == "question"
    assert (
        out.state.provisional_answers == {1: 0, 2: 0, 3: 1} and out.state.result is None
    )
    assert "Around five days" not in repr(out)
    state = out.state
    assert state.item_id == 4 and state.provisional_answers == {1: 0, 2: 0, 3: 1}
    assert state.clarification_item_id is None and not state.confirmed_answers
    assert send(state, "TEXT", item_id=4, text="只限上星期有幾天").state.item_id == 4


def test_c06_edit_context_clears_on_cancel_and_guard_before_provider():
    state = send(send(new_session(), "START").state, "ACCEPT").state
    state = send(state, "SELECT", item_id=1, value=0).state
    state = send(state, "EDIT", item_id=1).state
    state = send(state, "TEXT", item_id=1, text="可能有時").state
    assert state.clarification_item_id == 1
    cancelled = send(state, "CANCEL_EDIT").state
    assert (
        cancelled.clarification_item_id is None
        and cancelled.provisional_answers == {1: 0}
    )
    provider = Mock()
    stopped = dispatch(
        state,
        Event(
            "TEXT", state.session_id, state.revision, item_id=1, text="[DEMO_INTERRUPT]"
        ),
        nlu=provider,
    ).state
    provider.predict.assert_not_called()
    assert stopped.clarification_item_id is None and stopped.result is None
    assert not stopped.provisional_answers


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"timeframe": "missing"}, "timeframe_unverified"),
        ({"ambiguity": "contradiction", "confidence_signal": 1.0}, "contradiction"),
        ({"negation": "unclear"}, "negation_unclear"),
        ({"symptom_present": False}, "inconsistent_frequency"),
    ],
)
def test_c08_evidence_reason_does_not_accept_high_confidence_conflict(changes, reason):
    candidate = extract(1, "過去兩週有幾天") | changes
    result = evaluate_candidate(candidate, expected_item=1)
    assert result.value is None and result.reason == reason


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("過去兩週不是有幾天", "negation_unclear"),
        ("過去兩週不確定", "uncertain"),
        ("過去兩週完全沒有，但也說幾乎每天", "contradiction"),
    ],
)
def test_c08_default_provider_distinguishes_real_clarification_reasons(text, reason):
    state = send(send(new_session(), "START").state, "ACCEPT").state
    out = send(state, "TEXT", item_id=1, text=text)
    assert out.evidence_reason == reason and out.state.item_id == 1
    assert not out.state.provisional_answers and out.state.result is None
