"""Offline provider contracts. Callers supply the approved inference transport."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

from evidence_manager import evaluate_candidate
from nlu_provider import NluRequest
from schemas import NluResult, validate_nlu


@dataclass(frozen=True)
class SentimentResult:
    polarity: Literal["positive", "neutral", "negative", "mixed", "unavailable"]
    score: float | None
    version: str

    def __post_init__(self):
        if self.polarity not in {
            "positive",
            "neutral",
            "negative",
            "mixed",
            "unavailable",
        }:
            raise ValueError("Unknown polarity.")
        if not self.version or (
            self.score is not None
            and (type(self.score) not in {int, float} or not 0 <= self.score <= 1)
        ):
            raise ValueError("Invalid sentiment metadata.")
        if self.polarity == "unavailable" and self.score is not None:
            raise ValueError("Unavailable sentiment cannot carry a score.")


class SentimentProvider(Protocol):
    def predict(self, text: str) -> SentimentResult: ...


def sentiment_features(
    provider: SentimentProvider | None, text: str, evidence, item_id
):
    try:
        result = provider.predict(text) if provider is not None else None
        if not isinstance(result, SentimentResult):
            raise ValueError("Invalid sentiment result.")
    except Exception:
        result = SentimentResult("unavailable", None, "unavailable")
    candidate = evaluate_candidate(evidence, item_id).value
    mismatch = None
    if candidate is not None and result.polarity in {"positive", "neutral", "negative"}:
        mismatch = (candidate == 0 and result.polarity == "negative") or (
            candidate > 0 and result.polarity in {"neutral", "positive"}
        )
    return result, mismatch


@dataclass(frozen=True)
class TransportReply:
    payload: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost: float | None = None


@dataclass(frozen=True)
class ProviderRun:
    result: NluResult | None
    error: str | None
    attempts: int
    usage: tuple[tuple[int | None, int | None, float | None], ...]


def run_structured(request: NluRequest, transport: Callable, *, timeout=10, attempts=2):
    """The injected transport must enforce its timeout and return structured JSON."""
    if type(attempts) is not int or not 1 <= attempts <= 3 or not 0 < timeout <= 60:
        raise ValueError("Invalid request limits.")
    usage = []
    for attempt in range(1, attempts + 1):
        try:
            response = transport(request, timeout=timeout)
        except (TimeoutError, ConnectionError):
            continue
        if not isinstance(response, TransportReply):
            return ProviderRun(None, "invalid_response", attempt, tuple(usage))
        usage.append((response.input_tokens, response.output_tokens, response.cost))
        try:
            candidate = validate_nlu(json.loads(response.payload), request.item_id)
        except (TypeError, ValueError):
            return ProviderRun(None, "invalid_response", attempt, tuple(usage))
        return ProviderRun(candidate, None, attempt, tuple(usage))
    return ProviderRun(None, "transport_unavailable", attempts, tuple(usage))
