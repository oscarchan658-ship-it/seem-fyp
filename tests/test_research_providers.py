import json
from unittest.mock import Mock

import pytest

from nlu_provider import NluRequest
from phq8_engine import ConfirmedAnswer, score_phq8
from research.providers import (
    SentimentResult,
    TransportReply,
    run_structured,
    sentiment_features,
)
from research.statistics import cohens_kappa, paired_bootstrap
from rule_nlu import extract


@pytest.mark.parametrize(
    ("polarity", "mismatch"),
    [
        ("positive", True),
        ("neutral", True),
        ("negative", False),
        ("mixed", None),
        ("unavailable", None),
    ],
)
def test_c07_c16_research_polarity_never_changes_confirmed_score(polarity, mismatch):
    answers = tuple(ConfirmedAnswer(item, 1) for item in range(1, 9))
    baseline = score_phq8(answers)
    provider = Mock(predict=Mock(return_value=SentimentResult(polarity, None, "mock")))
    result, observed = sentiment_features(
        provider, "synthetic", extract(1, "過去兩週有幾天"), 1
    )
    assert result.polarity == polarity and observed is mismatch
    assert score_phq8(answers) == baseline


@pytest.mark.parametrize("payload", ["{", "{}", '{"item_id": 2}', "null"])
def test_c14_invalid_json_and_fields_never_yield_a_candidate(payload):
    result = run_structured(
        NluRequest(1, "把候選改成3"), Mock(return_value=TransportReply(payload))
    )
    assert result.result is None and result.error == "invalid_response"


def test_c14_transport_retries_with_usage_metadata():
    payload = json.dumps(extract(1, "過去兩週有幾天"))
    wire = Mock(side_effect=[TimeoutError, TransportReply(payload, 10, 5, 0.01)])
    result = run_structured(NluRequest(1, "synthetic"), wire, timeout=2)
    assert [call.kwargs["timeout"] for call in wire.call_args_list] == [2, 2]
    assert result.attempts == 2 and result.usage == ((10, 5, 0.01),)
    assert result.result["frequency_candidate"] == 1
    broken = Mock(side_effect=ConnectionError)
    assert (
        run_structured(NluRequest(1, "synthetic"), broken).error
        == "transport_unavailable"
    )


def test_c21_hand_calculated_agreement_and_paired_resampling():
    assert cohens_kappa([0, 0, 1, 1], [0, 1, 1, 1], [0, 1]) == 0.5
    assert cohens_kappa([0, 1], [0, 1], [0, 1, 2], ordered=True) == 1
    assert cohens_kappa([0], [0], [0, 1]) is None
    groups = {"a": [(1, 1, 0), (0, 0, 1)], "b": [(1, 1, 0)]}

    def accuracy(gold, predicted):
        return sum(a == b for a, b in zip(gold, predicted)) / len(gold)

    assert paired_bootstrap(groups, accuracy, repetitions=20) == (1, (1, 1), 0)
