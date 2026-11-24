import pytest

from controller import dispatch, new_session
from research.follow_up_oracle import FollowUpOracle, OracleReply
from schemas import Event


def test_c19_fixture_has_clarification_confirmation_correction_and_end():
    oracle = FollowUpOracle(
        {
            ("sleep-01", 1, "clarify-frequency"): OracleReply("有幾天"),
            ("sleep-01", 2, "confirm-candidate-2"): OracleReply("修正為有幾天"),
            ("sleep-01", 3, "confirm-candidate-1"): OracleReply("確認"),
            ("sleep-02", 1, "clarify-frequency"): OracleReply(None),
        }
    )
    assert oracle.respond("sleep-01", 1, "clarify-frequency").text == "有幾天"
    assert oracle.respond("sleep-01", 2, "confirm-candidate-2").text == "修正為有幾天"
    assert oracle.respond("sleep-01", 3, "confirm-candidate-1").text == "確認"
    assert oracle.respond("sleep-02", 1, "clarify-frequency").outcome == "unresolved"
    assert oracle.respond("sleep-01", 2, "malformed-action").outcome == "missing_branch"


def test_c19_oracle_rejects_invalid_turn_and_empty_reply():
    with pytest.raises(ValueError, match="turn"):
        FollowUpOracle({("case", 0, "clarify"): OracleReply("未確認")})
    with pytest.raises(ValueError, match="reply"):
        FollowUpOracle({("case", 1, "clarify"): OracleReply(" ")})


def test_c19_synthetic_eight_item_dialogue_keeps_score_provisional_until_confirmation():
    state = new_session()

    def send(kind, **fields):
        nonlocal state
        state = dispatch(
            state, Event(kind, state.session_id, state.revision, **fields)
        ).state

    send("START")
    send("ACCEPT")
    send("TEXT", item_id=1, text="過去兩週有時")
    assert state.phase == "CLARIFICATION" and not state.provisional_answers
    oracle = FollowUpOracle(
        {("demo", 1, "clarify-frequency"): OracleReply("過去兩週有幾天")}
    )
    answer = oracle.respond("demo", 1, "clarify-frequency")
    send("TEXT", item_id=1, text=answer.text)
    for item_id in range(2, 9):
        send("SELECT", item_id=item_id, value=0)
    assert state.phase == "BATCH_REVIEW" and state.result is None
    assert not state.confirmed_answers
    send("CONFIRM")
    assert state.result.total == 1 and len(state.confirmed_answers) == 8
