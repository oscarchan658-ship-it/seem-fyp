def test_oracle_freezes_actual_provider_predictions_and_explicit_confirmation(tmp_path):
    from research.oracle_predictions import freeze
    from research.e3_runner import run

    sessions = [
        dict(
            session_id="fixture",
            author_ref="human-fixture-test",
            items=[
                dict(
                    item_id=item,
                    case_id=f"f{item}",
                    gold_frequency=0,
                    initial_answer="not sure",
                    replies=[
                        dict(
                            turn=1,
                            action_id="clarify-frequency",
                            outcome="reply",
                            text="1 day",
                        ),
                        dict(
                            turn=2,
                            action_id="confirm-item",
                            outcome="reply",
                            confirmed_value=0,
                        ),
                    ],
                )
                for item in range(1, 9)
            ],
            batch=[
                dict(snapshot=[0] * 8, confirmed={str(item): 0 for item in range(1, 9)})
            ],
        )
    ]
    frozen = freeze(
        sessions,
        tmp_path / "frozen.json",
        config=dict(provider="rule", mode="synthetic"),
    )
    assert frozen[0]["items"][0]["replies"][0]["prediction"]["frequency_candidate"] == 0
    result = run(
        frozen,
        tmp_path / "e3",
        config=dict(provider="rule", mode="synthetic"),
        threshold_record=dict(status="NOT RUN"),
    )
    assert result["policies"]["P1"]["completion_rate"] == 1
    from research.e3_runner import load_frozen_sessions
    import pytest

    assert (
        load_frozen_sessions(
            tmp_path / "frozen.json", dict(provider="rule", mode="synthetic")
        )
        == frozen
    )
    with pytest.raises(ValueError, match="signature"):
        load_frozen_sessions(
            tmp_path / "frozen.json",
            dict(provider="rule", mode="synthetic", version="changed"),
        )
