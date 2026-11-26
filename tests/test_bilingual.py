from pathlib import Path
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest
from tests.test_app import click
from tests.test_conversation import engine, update
from localization import OPENING_EN

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_english_review_result_and_switch_preserve_state(monkeypatch):
    monkeypatch.setenv("FYP_API_KEY", "test-only")
    fake = engine([update(i, 0, "None of the eight symptoms") for i in range(1, 9)])
    factory = Mock(return_value=fake)
    monkeypatch.setattr("bilingual_provider.BilingualConversationProvider", factory)
    app = AppTest.from_file(str(APP)).run()
    app.selectbox(key="ui_language").select("en").run()
    click(app, "Start fictional conversation")
    assert app.session_state["conversation"].messages[0]["content"] == OPENING_EN
    app.chat_input[0].set_value("None of the eight symptoms").run()
    assert factory.call_args.kwargs["language"] == "en"
    original = app.session_state["conversation"]
    app.selectbox(key="ui_language").select("zh").run()
    assert app.session_state["conversation"] == original
    app.selectbox(key="ui_language").select("en").run()
    click(app, "Review summary")
    assert any(x.label == "Sleep difficulties: frequency" for x in app.selectbox)
    app.selectbox(key=f"review-{app.session_state['conversation'].revision}-3").select(
        2
    )
    app.checkbox[0].check()
    click(app, "Confirm and view score")
    assert app.metric[0].label == "PHQ-8 questionnaire total"
    assert app.metric[0].value == "2 / 24"
    app.selectbox(key="ui_language").select("zh").run()
    assert app.metric[0].label == "PHQ-8 問卷總分"
    assert app.metric[0].value == "2 / 24"


def test_english_failure_and_retry(monkeypatch):
    monkeypatch.setenv("FYP_API_KEY", "test-only")
    fake = engine()
    fake.respond.side_effect = TimeoutError
    monkeypatch.setattr(
        "bilingual_provider.BilingualConversationProvider", Mock(return_value=fake)
    )
    app = AppTest.from_file(str(APP)).run()
    app.selectbox(key="ui_language").select("en").run()
    click(app, "Start fictional conversation")
    app.chat_input[0].set_value("A fictional example.").run()
    assert any("AI could not reply" in w.value for w in app.warning)
    assert any(b.label == "Retry last message" for b in app.button)
    assert not app.metric


def test_provider_language_instruction_and_original_quotes(monkeypatch):
    from bilingual_provider import BilingualConversationProvider

    transport = Mock()
    monkeypatch.setattr("conversation.TerraClient", Mock(return_value=transport))
    p = BilingualConversationProvider(language="en")
    p.respond([{"role": "user", "content": "三日", "turn_id": 1}], {})
    args = transport.structured.call_args.args
    assert "Write every new reply and evidence summary in English" in args[0]
    assert args[1]["messages"][0]["content"] == "三日"
    assert args[1]["domains"]["3"] == "Sleep difficulties"
