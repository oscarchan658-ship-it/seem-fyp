from collections.abc import Mapping
from dataclasses import dataclass

from schemas import NluResult, validate_nlu


@dataclass(frozen=True)
class CandidateDecision:
    value: int | None
    reason: str


def assess_candidate(result: NluResult) -> CandidateDecision:
    if result["timeframe"] != "past_14_days":
        return CandidateDecision(None, "timeframe_unverified")
    if result["ambiguity"] == "contradiction":
        return CandidateDecision(None, "contradiction")
    if result["negation"] == "unclear":
        return CandidateDecision(None, "negation_unclear")
    if result["ambiguity"] != "none":
        return CandidateDecision(None, result["ambiguity"])
    value = result["frequency_candidate"]
    if value is None:
        return CandidateDecision(None, "frequency_missing")
    expected_negation = "clear" if value == 0 else "none"
    if (
        result["symptom_present"] is not (value > 0)
        or result["negation"] != expected_negation
    ):
        return CandidateDecision(None, "inconsistent_frequency")
    return CandidateDecision(value, "eligible")


def evaluate_candidate(
    payload: Mapping[str, object], expected_item: int
) -> CandidateDecision:
    return assess_candidate(validate_nlu(payload, expected_item))
