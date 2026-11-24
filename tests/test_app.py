from pathlib import Path
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def click(app, label):
    app.button(
        next(button.key for button in app.button if button.label == label)
    ).click().run()
    assert not app.exception
    return app


def open_app():
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    return app


def screening():
    return click(click(open_app(), "開始"), "同意並開始")


def test_t19_t20_t28_t30_t31_t33_web_review_edit_confirm_and_rerun():
    app = screening()
    assert app.title[0].value == "Sentiment Analysis for Depression Detection"
    options = ("完全沒有", "有幾天", "超過一半的日子", "幾乎每天")
    for label in options * 2:
        click(app, label)
    assert len(app.session_state["dialogue"].provisional_answers) == 8
    assert not app.metric
    app.run()
    assert not app.metric and not app.session_state["dialogue"].confirmed_answers
    click(app, "修改第 1 題")
    click(app, options[2])
    click(app, "確認八題答案並計分")
    assert app.metric[0].value == "14 / 24"
    app.run()
    assert app.metric[0].value == "14 / 24"


def test_t08_t32_private_state_and_clear():
    left, right = screening(), screening()
    left.chat_input[0].set_value("fictional-fyp-canary-5481").run()
    assert not left.exception
    assert left.session_state["dialogue"].phase == "CLARIFICATION"
    assert "fictional-fyp-canary-5481" not in repr(left.session_state)
    assert "fictional-fyp-canary-5481" not in str(left)
    click(left, "完全沒有")
    assert right.session_state["dialogue"].item_id == 1
    click(left, "取消問卷")
    assert not left.session_state["dialogue"].provisional_answers
    assert not left.chat_input and not left.metric
    initial_id = left.session_state["dialogue"].session_id
    click(left, "重新開始")
    assert left.session_state["dialogue"].session_id != initial_id


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("[DEMO_INTERRUPT]", "模擬中斷"),
        ("[DEMO_REVIEW]", "模擬覆核"),
    ],
)
def test_t23_t29_t31_safety_mock_stops_form_and_clear_input(text, expected):
    app = screening()
    click(app, "完全沒有")
    app.chat_input[0].set_value(text).run()
    assert not app.exception
    assert expected in app.warning[0].value
    assert not app.session_state["dialogue"].provisional_answers
    assert not app.metric and not app.chat_input and text not in repr(app.session_state)
    app.run()
    assert expected in app.warning[0].value


def test_t24_invalid_nlu_gives_selection_fallback(monkeypatch):
    import controller

    dispatch = controller.dispatch
    broken = Mock(return_value={})
    monkeypatch.setattr(
        controller,
        "dispatch",
        lambda state, event: dispatch(state, event, nlu=Mock(predict=broken)),
    )
    app = screening()
    app.chat_input[0].set_value("synthetic").run()
    assert not app.exception and "暫時無法解讀" in app.info[0].value
    click(app, "完全沒有")
    assert app.session_state["dialogue"].item_id == 2
    for _ in range(7):
        click(app, "完全沒有")
    click(app, "確認八題答案並計分")
    assert app.metric[0].value == "0 / 24"


def test_t23_coalesced_confirm_cannot_precede_safety_text(monkeypatch):
    app = screening()
    for _ in range(8):
        click(app, "完全沒有")
    scorer = Mock(side_effect=AssertionError("Safety must run before scoring."))
    monkeypatch.setattr("controller.score_phq8", scorer)
    next(
        button for button in app.button if button.label == "確認八題答案並計分"
    ).click()
    app.chat_input[0].set_value("[DEMO_INTERRUPT]")
    app.run()
    scorer.assert_not_called()
    assert app.session_state["dialogue"].phase == "SAFETY_FLOW"
    assert "模擬中斷" in app.warning[0].value
    assert not app.metric


@pytest.mark.parametrize(
    "guard", [Mock(return_value=[]), Mock(side_effect=RuntimeError)]
)
def test_t29_guard_failure_shows_fixed_message(monkeypatch, guard):
    import controller

    dispatch = controller.dispatch
    monkeypatch.setattr(
        controller, "dispatch", lambda state, event: dispatch(state, event, guard=guard)
    )
    app = screening()
    app.chat_input[0].set_value("synthetic").run()
    assert not app.exception
    assert "測試守門模組未能回應" in app.warning[0].value
    assert not app.chat_input and not app.metric
    app.run()
    assert "測試守門模組未能回應" in app.warning[0].value
