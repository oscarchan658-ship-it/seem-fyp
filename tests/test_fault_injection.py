from unittest.mock import Mock

from controller import dispatch, new_session
from schemas import Event


def test_c23_c27_timeout_during_edit_and_guard_failure_during_retry():
    state = new_session()

    def event(kind, **fields):
        return Event(kind, state.session_id, state.revision, **fields)

    for kind, fields in [
        ("START", {}),
        ("ACCEPT", {}),
        ("SELECT", {"item_id": 1, "value": 0}),
        ("EDIT", {"item_id": 1}),
    ]:
        state = dispatch(state, event(kind, **fields)).state
    text = event("TEXT", item_id=1, text="synthetic timeout fixture")
    provider = Mock(side_effect=TimeoutError)
    unavailable = dispatch(state, text, nlu=provider)
    state = unavailable.state
    assert unavailable.response_code == "nlu_unavailable"
    assert state.phase == "EDIT_ANSWER" and state.provisional_answers == {1: 0}
    assert state.result is None and not state.confirmed_answers
    provider.reset_mock()

    interrupted = dispatch(
        state, text, nlu=provider, guard=Mock(side_effect=TimeoutError)
    )
    state = interrupted.state
    assert (
        interrupted.response_code == "safety_unavailable"
        and state.phase == "SAFETY_FLOW"
    )
    assert not state.provisional_answers and not state.confirmed_answers
    assert state.result is None
    assert dispatch(state, text).state is state
    provider.assert_not_called()
    assert dispatch(state, event("RESET")).state.session_id != state.session_id
