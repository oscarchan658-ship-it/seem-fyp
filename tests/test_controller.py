from unittest.mock import Mock

import pytest

from controller import dispatch, new_session
from schemas import Event


def event(state, kind, **payload):
    return Event(kind, state.session_id, state.revision, **payload)


def step(state, kind, **payload):
    return dispatch(state, event(state, kind, **payload)).state


def screening():
    return step(step(new_session(), "START"), "ACCEPT")


def review():
    state = screening()
    for item_id, value in enumerate([0, 1, 2, 3] * 2, 1):
        state = step(state, "SELECT", item_id=item_id, value=value)
    return state


def test_t06_t08_t17_t26_illegal_replayed_and_cancelled_events():
    start = new_session()
    assert step(start, "CONFIRM") is start
    consent = step(start, "START")
    assert step(consent, "SELECT", item_id=1, value=0) is consent
    assert step(consent, "DECLINE").phase == "END"
    state = step(consent, "ACCEPT")
    choose = event(state, "SELECT", item_id=1, value=0)
    assert step(state, "SELECT", item_id=2, value=0) is state
    assert step(state, "SELECT", item_id=1, value=True) is state
    picked = dispatch(state, choose).state
    assert picked.item_id == 2 and picked.provisional_answers == {1: 0}
    assert dispatch(picked, choose).state is picked
    assert dispatch(screening(), choose).response_code == "rejected"
    ended = step(picked, "CANCEL")
    assert ended.phase == "END" and not ended.provisional_answers
    assert dispatch(ended, choose).state is ended


def test_t07_t18_t19_t20_confirm_latest_snapshot_only(monkeypatch):
    import controller

    scorer = Mock(wraps=controller.score_phq8)
    monkeypatch.setattr(controller, "score_phq8", scorer)
    state = review()
    assert state.phase == "BATCH_REVIEW"
    assert not state.confirmed_answers and state.result is None
    old_confirm = event(state, "CONFIRM")
    editing = step(state, "EDIT", item_id=1)
    bad = step(editing, "TEXT", item_id=1, text="不確定")
    assert bad.phase == "EDIT_ANSWER" and bad.provisional_answers[1] == 0
    assert step(bad, "CANCEL_EDIT").provisional_answers[1] == 0
    updated = step(editing, "SELECT", item_id=1, value=2)
    assert updated.phase == "BATCH_REVIEW"
    assert dispatch(updated, old_confirm).state is updated
    scorer.assert_not_called()
    confirm = event(updated, "CONFIRM")
    done = dispatch(updated, confirm).state
    assert done.phase == "RESULT" and done.result.total == 14
    assert len(done.confirmed_answers) == 8
    assert dispatch(done, confirm).state is done
    assert step(done, "EDIT", item_id=1) is done
    scorer.assert_called_once()


def test_t18_edit_from_screening_restores_original_question():
    state = step(screening(), "SELECT", item_id=1, value=1)
    editing = step(state, "EDIT", item_id=1)
    updated = step(editing, "SELECT", item_id=1, value=3)
    assert (updated.phase, updated.item_id) == ("SCREENING", 2)
    assert updated.provisional_answers == {1: 3}


def test_t20_confirms_unedited_batch():
    done = step(review(), "CONFIRM")
    assert done.phase == "RESULT" and done.result.total == 12


@pytest.mark.parametrize(
    "phase",
    ["START", "CONSENT", "SCREENING", "CLARIFICATION", "EDIT_ANSWER", "BATCH_REVIEW"],
)
def test_t23_safety_wins_before_stale_and_off_topic_checks(phase, monkeypatch):
    start = new_session()
    active = screening()
    answered = step(active, "SELECT", item_id=1, value=1)
    states = {
        "START": start,
        "CONSENT": step(start, "START"),
        "SCREENING": active,
        "CLARIFICATION": step(active, "TEXT", item_id=1, text="不確定"),
        "EDIT_ANSWER": step(answered, "EDIT", item_id=1),
        "BATCH_REVIEW": review(),
    }
    before = states[phase]
    nlu, scorer = Mock(), Mock()
    monkeypatch.setattr("controller.score_phq8", scorer)
    text = Event("TEXT", before.session_id, -1, item_id=99, text="synthetic signal")
    out = dispatch(
        before, text, guard=Mock(return_value="interrupt"), nlu=Mock(predict=nlu)
    )
    assert out.response_code == "safety_interrupt"
    stopped = out.state
    assert stopped.phase == "SAFETY_FLOW"
    assert not stopped.provisional_answers and not stopped.confirmed_answers
    assert stopped.result is None and "synthetic signal" not in repr(out)
    assert step(stopped, "CONFIRM") is stopped
    fresh = step(stopped, "RESET")
    assert fresh.phase == "START" and fresh.session_id != stopped.session_id
    assert dispatch(fresh, text, guard=Mock(return_value="interrupt")).state is fresh
    nlu.assert_not_called()
    scorer.assert_not_called()


@pytest.mark.parametrize(
    ("guard", "code"),
    [
        (Mock(return_value="review"), "safety_review"),
        (Mock(return_value=[]), "safety_unavailable"),
        (Mock(side_effect=RuntimeError), "safety_unavailable"),
    ],
)
def test_t29_safety_review_and_guard_failure_block(guard, code, monkeypatch):
    state = review()
    nlu, scorer = Mock(), Mock()
    monkeypatch.setattr("controller.score_phq8", scorer)
    out = dispatch(
        state,
        event(state, "TEXT", text="synthetic"),
        guard=guard,
        nlu=Mock(predict=nlu),
    )
    assert out.state.phase == "SAFETY_FLOW" and out.response_code == code
    assert not out.state.provisional_answers
    assert step(out.state, "CONFIRM") is out.state
    nlu.assert_not_called()
    scorer.assert_not_called()


@pytest.mark.parametrize("nlu", [Mock(side_effect=RuntimeError), Mock(return_value={})])
def test_t24_nlu_failure_preserves_answers_and_allows_selection(nlu):
    state = step(screening(), "SELECT", item_id=1, value=0)
    out = dispatch(
        state, event(state, "TEXT", item_id=2, text="synthetic"), nlu=Mock(predict=nlu)
    )
    assert out.response_code == "nlu_unavailable"
    assert (out.state.phase, out.state.item_id) == ("CLARIFICATION", 2)
    assert out.state.provisional_answers == {1: 0}
    assert step(out.state, "SELECT", item_id=2, value=3).provisional_answers == {
        1: 0,
        2: 3,
    }


@pytest.mark.parametrize("fault", [ValueError, RuntimeError])
def test_t28_score_failure_is_atomic(monkeypatch, fault):
    state = review()
    monkeypatch.setattr("controller.score_phq8", Mock(side_effect=fault))
    out = dispatch(state, event(state, "CONFIRM"))
    assert out.response_code == "scoring_unavailable" and out.state is state
    assert not out.state.confirmed_answers and out.state.result is None


def test_t36_cross_session_text_is_rejected_before_guard_and_nlu():
    state = screening()
    guard = Mock(side_effect=AssertionError("Must not inspect another session"))
    nlu = Mock()
    foreign = Event("TEXT", "foreign-session", -1, item_id=99, text="[DEMO_INTERRUPT]")
    out = dispatch(state, foreign, guard=guard, nlu=Mock(predict=nlu))
    assert out.response_code == "rejected" and out.state is state
    guard.assert_not_called()
    nlu.assert_not_called()


@pytest.mark.parametrize(
    ("guard_result", "expected_code", "expected_phase"),
    [
        ("normal", "rejected", "SCREENING"),
        ("review", "safety_review", "SAFETY_FLOW"),
        ("interrupt", "safety_interrupt", "SAFETY_FLOW"),
    ],
)
def test_t36_same_session_stale_text_runs_guard_before_revision_validation(
    guard_result, expected_code, expected_phase
):
    state = screening()
    guard, nlu = Mock(return_value=guard_result), Mock()
    stale = Event(
        "TEXT",
        state.session_id,
        state.revision - 1,
        item_id=99,
        text="synthetic stale event",
    )
    out = dispatch(state, stale, guard=guard, nlu=Mock(predict=nlu))
    assert (out.response_code, out.state.phase) == (expected_code, expected_phase)
    guard.assert_called_once_with("synthetic stale event")
    nlu.assert_not_called()
    if expected_phase == "SCREENING":
        assert out.state is state
    else:
        assert not out.state.provisional_answers
        assert out.state.result is None


def test_t36_select_input_does_not_invoke_text_guard():
    state = screening()
    guard = Mock(side_effect=AssertionError("Structured choice is not free text"))
    out = dispatch(state, event(state, "SELECT", item_id=1, value=2), guard=guard)
    assert out.response_code == "question"
    assert out.state.provisional_answers == {1: 2}
    guard.assert_not_called()
