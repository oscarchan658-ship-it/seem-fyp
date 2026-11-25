from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, NotRequired, TypedDict, cast

from phq8_engine import ConfirmedAnswer, Phq8Result


class NluResult(TypedDict):
    item_id: int
    frequency_candidate: int | None
    timeframe: Literal["past_14_days", "missing", "other", "unclear"]
    symptom_present: bool | None
    negation: Literal["none", "clear", "unclear"]
    ambiguity: Literal[
        "none", "ambiguous_frequency", "uncertain", "contradiction", "off_topic"
    ]
    model_version: str
    confidence_signal: NotRequired[int | float | None]


class LocalDayResult(dict):
    """In-process day evidence. JSON deserialization cannot construct this type."""

    def __init__(self, payload, interval):
        super().__init__(payload)
        self.interval = tuple(interval)


def validate_nlu(payload: Mapping[str, object], expected_item: int) -> NluResult:
    if not isinstance(payload, Mapping):
        raise ValueError("Expected an NLU object.")
    keys = set(payload)
    if keys - {"confidence_signal"} != NluResult.__required_keys__:
        raise ValueError("Unexpected or missing NLU fields.")

    item_id = payload["item_id"]
    value = payload["frequency_candidate"]
    confidence = payload.get("confidence_signal")
    present = payload["symptom_present"]
    version = payload["model_version"]
    if type(item_id) is not int or not 1 <= item_id <= 8 or item_id != expected_item:
        raise ValueError("Unexpected item_id.")
    if value is not None and (type(value) is not int or not 0 <= value <= 3):
        raise ValueError("Invalid frequency candidate.")
    if confidence is not None and (
        type(confidence) not in (float, int) or not 0 <= confidence <= 1
    ):
        raise ValueError("Invalid confidence signal.")
    if present is not None and type(present) is not bool:
        raise ValueError("Invalid symptom presence.")
    if type(version) is not str or not version.strip():
        raise ValueError("Invalid model version.")
    for key, choices in (
        ("timeframe", ("past_14_days", "missing", "other", "unclear")),
        ("negation", ("none", "clear", "unclear")),
        (
            "ambiguity",
            ("none", "ambiguous_frequency", "uncertain", "contradiction", "off_topic"),
        ),
    ):
        if type(payload[key]) is not str or payload[key] not in choices:
            raise ValueError(f"Invalid {key}.")
    if type(payload) is LocalDayResult:
        return cast(NluResult, LocalDayResult(payload, payload.interval))
    return cast(NluResult, dict(payload))


@dataclass(frozen=True)
class Event:
    kind: str
    session_id: str
    expected_revision: int
    item_id: int | None = None
    value: int | None = None
    text: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class SessionState:
    session_id: str
    phase: str = "START"
    revision: int = 0
    item_id: int | None = None
    return_to: tuple[str, int | None] | None = None
    provisional_answers: Mapping[int, int] = field(
        default_factory=lambda: MappingProxyType({})
    )
    confirmed_answers: tuple[ConfirmedAnswer, ...] = ()
    safety_state: str | None = None
    result: Phq8Result | None = None
    clarification_item_id: int | None = None


@dataclass(frozen=True)
class Transition:
    state: SessionState
    response_code: str
    previous_phase: str
    event_kind: str
    item_id: int | None
    evidence_reason: str | None = None
