from collections.abc import Mapping
from dataclasses import dataclass

from schemas import LocalDayResult, NluResult, validate_nlu
from research.day_mapping import map_days


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
    if type(result) is LocalDayResult:
        lower, upper = result.interval
        mapped = map_days(lower, upper)
        present = False if upper == 0 else True if lower > 0 else None
        negation = "clear" if upper == 0 else "none"
        if (
            mapped != value
            or result["symptom_present"] is not present
            or result["negation"] != negation
        ):
            return CandidateDecision(None, "inconsistent_day_evidence")
        return CandidateDecision(value, "eligible")
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
