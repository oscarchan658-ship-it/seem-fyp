from unittest.mock import Mock
import pytest
from conversation import (
    chat_turn,
    new_conversation,
    open_review,
    confirm_review,
    retry_turn,
    ready,
    validate_proposal,
)


def proposal(updates=(), reply="你提到睡不好。過去兩星期大概有幾天？"):
    return {"reply": reply, "sentiment": "negative", "updates": list(updates)}


def update(item=3, value=3, quote="每天睡不好", turn=1):
    return {
        "item_id": item,
        "frequency": value,
        "timeframe": "past_14_days",
        "quote": quote,
        "turn_id": turn,
        "summary": "過去兩星期每天睡不好",
    }


def engine(updates=()):
    return Mock(
        respond=Mock(return_value=(proposal(updates), {"reported_model": "mock"}))
    )


def test_multi_domain_context_and_no_score_until_confirmation():
    p = engine([update(), update(4, 2, "八天很累")])
    s = chat_turn(new_conversation(), "每天睡不好，八天很累", p)
    assert set(s.candidates) == {3, 4} and s.result is None
    assert len(s.messages) == 3 and not ready(s)
    p.respond.return_value = (proposal([update(2, 1, "有幾天心情低落", 3)]), {})
    s = chat_turn(s, "有幾天心情低落", p)
    assert len(p.respond.call_args.args[0]) == 4
    assert set(s.candidates) == {2, 3, 4}


def test_guard_clears_history_before_remote_call():
    p = engine([update()])
    s = chat_turn(new_conversation(), "每天睡不好", p)
    p.reset_mock()
    s = chat_turn(s, "[DEMO_INTERRUPT]", p)
    p.respond.assert_not_called()
    assert s.phase == "PAUSED" and not s.messages and not s.candidates


@pytest.mark.parametrize(
    "change",
    [
        {"frequency": True},
        {"frequency": 4},
        {"frequency": 1.0},
        {"quote": "fabricated quote"},
        {"turn_id": 0},
        {"timeframe": "other"},
    ],
)
def test_invalid_proposal_is_atomic_and_no_score(change):
    u = update()
    u.update(change)
    s = chat_turn(new_conversation(), "每天睡不好", engine([u]))
    assert s.error and not s.candidates and s.result is None


def test_duplicate_item_rejected():
    with pytest.raises(ValueError):
        validate_proposal(
            proposal([update(), update()]),
            [{"role": "user", "content": "每天睡不好", "turn_id": 1}],
        )


def test_correction_invalidates_answer_and_review():
    s = chat_turn(new_conversation(), "每天睡不好", engine([update()]))
    s = chat_turn(s, "其實我不確定有幾天", engine([update(3, None, "不確定有幾天", 3)]))
    assert s.candidates[3]["frequency"] is None and not ready(s)


def test_complete_review_requires_consent_revision_and_strict_values():
    s = chat_turn(
        new_conversation(),
        "所有八項都完全沒有",
        engine([update(i, 0, "所有八項都完全沒有") for i in range(1, 9)]),
    )
    assert ready(s) and s.result is None
    s = open_review(s)
    vals = dict.fromkeys(range(1, 9), 0)
    for consent, rev in [(False, s.revision), (True, s.revision - 1)]:
        with pytest.raises(ValueError):
            confirm_review(s, vals, expected_revision=rev, consent=consent)
    with pytest.raises(ValueError):
        confirm_review(s, {**vals, 1: True}, expected_revision=s.revision, consent=True)
    out = confirm_review(s, {**vals, 3: 2}, expected_revision=s.revision, consent=True)
    assert out.result.total == 2
    assert chat_turn(out, "new", engine()) == out


def test_failed_call_retry_does_not_duplicate_user_or_confirm_old_review():
    p = engine()
    p.respond.side_effect = TimeoutError
    s = chat_turn(new_conversation(), "每天睡不好", p)
    assert s.error and len(s.messages) == 2
    s = retry_turn(s, engine([update()]))
    assert not s.error and len(s.messages) == 3
    assert s.candidates[3]["frequency"] == 3


def test_web_chat_and_review(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from tests.test_app import click

    monkeypatch.setenv("FYP_API_KEY", "test-only")
    p = engine([update(i, 0, "所有八項都完全沒有") for i in range(1, 9)])
    monkeypatch.setattr(
        "bilingual_provider.BilingualConversationProvider", Mock(return_value=p)
    )
    app = AppTest.from_file(
        str(__import__("pathlib").Path(__file__).resolve().parents[1] / "app.py")
    ).run()
    click(app, "開始虛構對話")
    app.chat_input[0].set_value("所有八項都完全沒有").run()
    assert not app.exception and len(app.chat_message) == 3
    assert not app.metric
    click(app, "核對整理內容")
    click(app, "確認並查看分數")
    assert not app.metric
    app.checkbox[0].check()
    click(app, "確認並查看分數")
    assert app.metric[0].value == "0 / 24"
    click(app, "清除對話並重新開始")
    assert not app.session_state["conversation"].candidates
    assert len(app.session_state["conversation"].messages) == 1


def at_turn_limit(complete=True):
    from dataclasses import replace

    s = chat_turn(
        new_conversation(),
        "所有八項都完全沒有",
        engine(
            [update(i, 0, "所有八項都完全沒有") for i in range(1, 9)]
            if complete
            else []
        ),
    )
    messages = list(s.messages)
    for _ in range(39):
        messages.append({"role": "user", "content": "補充", "turn_id": len(messages)})
        messages.append(
            {"role": "assistant", "content": "收到", "turn_id": len(messages)}
        )
    return replace(s, messages=tuple(messages))


def test_turn_cap_preserves_review_and_blocks_extra_calls():
    p = engine()
    state = at_turn_limit()
    assert chat_turn(state, "額外一句", p) == state
    p.respond.assert_not_called()
    reviewed = open_review(state)
    assert (
        confirm_review(
            reviewed,
            dict.fromkeys(range(1, 9), 0),
            expected_revision=reviewed.revision,
            consent=True,
        ).result.total
        == 0
    )
    incomplete = at_turn_limit(complete=False)
    assert not ready(incomplete)
    assert open_review(incomplete) == incomplete
    interrupted = chat_turn(state, "[DEMO_INTERRUPT]", p)
    assert interrupted.phase == "PAUSED" and not interrupted.messages


def test_fortieth_failed_turn_can_retry_without_allowing_forty_first():
    from dataclasses import replace
    from conversation import turn_limit_reached

    state = replace(at_turn_limit(), messages=at_turn_limit().messages[:-2])
    p = engine()
    p.respond.side_effect = TimeoutError
    failed = chat_turn(state, "最後補充", p)
    assert failed.error and turn_limit_reached(failed)
    recovered = retry_turn(failed, engine())
    assert not recovered.error and turn_limit_reached(recovered)
    assert len(recovered.messages) == 81
    p.reset_mock()
    assert chat_turn(recovered, "另一句", p) == recovered
    p.respond.assert_not_called()


def test_web_turn_limit_keeps_complete_review_available(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    from tests.test_app import click

    monkeypatch.setenv("FYP_API_KEY", "test-only")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.session_state["chat_consent"] = True
    app.session_state["conversation"] = at_turn_limit()
    app.run()
    assert app.chat_input[0].disabled and not app.exception
    click(app, "核對整理內容")
    app.checkbox[0].check()
    click(app, "確認並查看分數")
    assert app.metric[0].value == "0 / 24"
