from rule_nlu import extract


def test_e3_full_questionnaire_outputs_with_frozen_oracle(tmp_path):
    from research.e3_runner import run

    payload = extract(1, "過去兩週有幾天")
    items = [
        dict(
            item_id=item,
            case_id=f"c{item}",
            gold_frequency=1,
            initial=dict(payload, item_id=item),
            replies=[
                dict(
                    turn=1, action_id="confirm-item", outcome="reply", confirmed_value=1
                )
            ],
        )
        for item in range(1, 9)
    ]
    data = [
        dict(
            session_id="s1",
            items=items,
            batch=[
                dict(snapshot=[1] * 8, confirmed={str(item): 1 for item in range(1, 9)})
            ],
        )
    ]
    result = run(
        data,
        tmp_path / "e3",
        config=dict(provider="rule", mode="synthetic"),
        threshold_record=dict(status="NOT RUN", threshold=None),
    )
    assert result["policies"]["P1"]["completion_rate"] == 1
    assert result["policies"]["P1"]["confirmation_actions"] == 1
    assert result["policies"]["P2"]["status"] == "NOT RUN"
    assert (tmp_path / "e3/e3_case_traces.jsonl").exists()


def test_sentiment_divergence_reads_symptom_fact_for_one_day():
    from nlu_provider import ClarificationContext, NluRequest, RuleProvider
    from research.providers import SentimentResult, sentiment_features

    class Neutral:
        def predict(self, text):
            return SentimentResult("neutral", 0.9, "fixture")

    payload = RuleProvider().predict(
        NluRequest(
            1,
            "1 day",
            clarification=ClarificationContext(1, "frequency_in_past_14_days"),
        )
    )
    assert (
        sentiment_features(Neutral(), "synthetic", payload, 1).affect_symptom_divergence
        is True
    )


def test_e3_rule_day_evidence_round_trips_json(tmp_path):
    import json
    from nlu_provider import ClarificationContext, NluRequest, RuleProvider
    from research.e3_runner import run

    items = []
    for item in range(1, 9):
        request = NluRequest(
            item,
            "1 day",
            clarification=ClarificationContext(item, "frequency_in_past_14_days"),
        )
        items.append(
            dict(
                item_id=item,
                case_id=f"day-{item}",
                gold_frequency=0,
                initial=RuleProvider().predict(request),
                initial_request=dict(text="1 day", clarification=True),
                replies=[],
            )
        )
    sessions = json.loads(
        json.dumps(
            [
                dict(
                    session_id="roundtrip",
                    items=items,
                    batch=[
                        dict(
                            snapshot=[0] * 8,
                            confirmed={str(item): 0 for item in range(1, 9)},
                        )
                    ],
                )
            ]
        )
    )
    result = run(
        sessions,
        tmp_path / "roundtrip",
        config=dict(provider="rule", mode="synthetic"),
        threshold_record=dict(status="NOT RUN", threshold=None),
    )
    assert result["policies"]["P1"]["completion_rate"] == 1


def test_e3_frozen_grid_produces_locked_curve_and_rejects_other_model(tmp_path):
    import pytest
    from research.e3_runner import run
    from research.local_models import model_signature

    config = dict(provider="fixture", mode="synthetic", version="fixture-v1")
    items = [
        dict(
            item_id=item,
            case_id=f"f{item}",
            gold_frequency=1,
            initial=dict(
                extract(item, "過去兩週有幾天"),
                model_version="fixture-v1",
                confidence_signal=0.9,
            ),
            replies=[
                dict(
                    turn=1, action_id="confirm-item", outcome="reply", confirmed_value=1
                )
            ],
        )
        for item in range(1, 9)
    ]
    sessions = [
        dict(
            session_id="fixture",
            items=items,
            batch=[
                dict(snapshot=[1] * 8, confirmed={str(item): 1 for item in range(1, 9)})
            ],
        )
    ]
    record = dict(
        status="FROZEN",
        threshold=0.9,
        grid=[0, 0.9, 1],
        model_signature=model_signature(config),
        model_versions=["fixture-v1"],
        selection_turn="initial",
        validation_sha256="fixture-hash",
    )
    result = run(sessions, tmp_path / "curve", config=config, threshold_record=record)
    assert (tmp_path / "curve/risk_coverage.csv").exists()
    assert result["policies"]["P3"]["completion_rate"] == 1
    with pytest.raises(ValueError, match="model"):
        run(
            sessions,
            tmp_path / "other",
            config=dict(config, version="different"),
            threshold_record=record,
        )
