from unittest.mock import Mock

from sentiment_service import analyze
from terra_client import acknowledgment


def test_chinese_is_not_sent_to_english_model(monkeypatch):
    model = Mock(side_effect=AssertionError("English model must not run"))
    monkeypatch.setattr("sentiment_service.local_model", model)
    assert analyze("我很開心", "local")[0] == "unavailable"
    model.assert_not_called()


def test_provider_failure_returns_neutral_fallback(monkeypatch):
    monkeypatch.setattr("sentiment_service.TerraClient", Mock(side_effect=ValueError))
    assert analyze("fictional", "terra")[0] == "unavailable"
    assert acknowledgment("unavailable")


def test_sentiment_is_after_guard_and_does_not_change_score(monkeypatch):
    from tests.test_app import screening, click

    model = Mock(return_value=("negative", "test mock"))
    monkeypatch.setattr("sentiment_service.analyze", model)
    app = screening()
    app.selectbox[0].select("terra").run()
    app.chat_input[0].set_value("過去兩週有幾天").run()
    assert app.session_state["dialogue"].provisional_answers == {1: 1}
    assert model.call_count == 1
    for _ in range(7):
        click(app, "完全沒有")
    click(app, "確認八題答案並計分")
    assert app.metric[0].value == "1 / 24"
    click(app, "重新開始")
    click(app, "開始")
    click(app, "同意並開始")
    app.chat_input[0].set_value("[DEMO_INTERRUPT]").run()
    assert model.call_count == 1
    assert "sentiment_summary" not in app.session_state
