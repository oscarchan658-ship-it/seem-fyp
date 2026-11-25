import pytest

from controller import dispatch, new_session
from evidence_manager import evaluate_candidate
from nlu_provider import ClarificationContext, NluRequest, RuleProvider
from schemas import Event, validate_nlu


@pytest.mark.parametrize(
    ("days", "value"),
    [(0, 0), (1, 0), (2, 1), (6, 1), (7, 2), (11, 2), (12, 3), (14, 3)],
)
def test_r1_boundaries(days, value):
    from research.day_mapping import map_days

    assert map_days(days, days) == value


@pytest.mark.parametrize("days", [-1, 15, 1.0, True, "1"])
def test_r1_invalid(days):
    from research.day_mapping import map_days

    with pytest.raises(ValueError):
        map_days(days, days)


@pytest.mark.parametrize(
    ("text", "value", "present"),
    [
        ("Around five days", 1, True),
        ("1 day", 0, True),
        ("0 days", 0, False),
        ("about 0 days", 0, None),
        ("around 6–7 days", None, True),
        ("around 11-12 days", None, True),
        ("大約五天", 1, True),
        ("約6至7天", None, True),
        ("1天", 0, True),
    ],
)
def test_r1_local_evidence_and_context(text, value, present):
    provider = RuleProvider()
    request = NluRequest(
        3, text, clarification=ClarificationContext(3, "frequency_in_past_14_days")
    )
    payload = provider.predict(request)
    assert evaluate_candidate(payload, 3).value == value
    assert payload["symptom_present"] is present
    assert evaluate_candidate(provider.predict(NluRequest(3, text)), 3).value is None
    assert (
        evaluate_candidate(
            provider.predict(NluRequest(4, text, clarification=request.clarification)),
            4,
        ).value
        is None
    )


def test_r1_external_json_cannot_claim_local_interval():
    candidate = RuleProvider().predict(
        NluRequest(
            1,
            "1 day",
            clarification=ClarificationContext(1, "frequency_in_past_14_days"),
        )
    )
    with pytest.raises(ValueError):
        validate_nlu(dict(candidate, day_interval=[1, 1]), 1)
    ordinary = dict(candidate)
    ordinary.pop("day_interval", None)
    assert evaluate_candidate(ordinary, 1).value is None


def test_r1_controller_stores_zero_without_confirming_or_scoring():
    def send(state, kind, **payload):
        return dispatch(state, Event(kind, state.session_id, state.revision, **payload))

    state = send(send(new_session(), "START").state, "ACCEPT").state
    state = send(state, "TEXT", item_id=1, text="not sure").state
    state = send(state, "TEXT", item_id=1, text="1 day").state
    assert state.provisional_answers == {1: 0}
    assert not state.confirmed_answers and state.result is None


def test_reset_during_clarification_cannot_reuse_or_partially_clear_answers():
    state = dispatch(new_session(), Event("START", "invalid", 0)).state
    state = dispatch(state, Event("START", state.session_id, state.revision)).state
    state = dispatch(state, Event("ACCEPT", state.session_id, state.revision)).state
    state = dispatch(
        state,
        Event("TEXT", state.session_id, state.revision, item_id=1, text="not sure"),
    ).state
    rejected = dispatch(state, Event("RESET", state.session_id, state.revision))
    assert rejected.response_code == "rejected" and rejected.state is state
