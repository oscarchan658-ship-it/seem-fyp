from controller import dispatch, new_session
from schemas import Event
from answer_display import describe_answer


def send(state, kind, **kwargs):
    return dispatch(
        state, Event(kind, state.session_id, state.revision, **kwargs)
    ).state


def test_day_evidence_survives_review_but_is_replaced_on_edit_and_cleared():
    state = send(send(new_session(), "START"), "ACCEPT")
    state = send(state, "TEXT", item_id=1, text="不確定")
    state = send(state, "TEXT", item_id=1, text="1 day")
    assert state.day_intervals[1] == (1, 1)
    for item in range(2, 9):
        state = send(state, "SELECT", item_id=item, value=0)
    assert "1 天" in describe_answer(state, 1)
    assert "完全沒有" not in describe_answer(state, 1)
    assert state.result is None
    state = send(state, "EDIT", item_id=1)
    state = send(state, "SELECT", item_id=1, value=1)
    assert not state.day_intervals
    assert describe_answer(state, 1) == "有幾天"
    state = send(state, "CONFIRM")
    assert state.result.total == 1
    assert not send(state, "CANCEL").day_intervals


def test_web_review_explains_one_day_instead_of_absence():
    from tests.test_app import screening, click

    app = screening()
    app.chat_input[0].set_value("不確定").run()
    app.chat_input[0].set_value("1 day").run()
    for _ in range(7):
        click(app, "完全沒有")
    assert any("1 天" in element.value for element in app.markdown)
    click(app, "確認八題答案並計分")
    assert app.metric[0].value == "0 / 24"
