"""Context-aware candidate interface; day evidence remains unscored."""

import re
from dataclasses import dataclass, field
from typing import Literal, Protocol

from rule_nlu import extract
from schemas import NluResult

_DAY_WORDS = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
)
_DAYS = re.compile(
    r"(?:(around|about)\s+)?(\d{1,2}|" + "|".join(_DAY_WORDS) + r")\s+days?"
)


@dataclass(frozen=True)
class ClarificationContext:
    item_id: int
    question: Literal["frequency_in_past_14_days"]


@dataclass(frozen=True)
class NluRequest:
    item_id: int
    text: str = field(repr=False)
    question_timeframe: Literal["past_14_days", "missing"] = "past_14_days"
    clarification: ClarificationContext | None = None


@dataclass(frozen=True)
class DayEvidence:
    count: int
    approximate: bool


class NLUProvider(Protocol):
    def predict(self, request: NluRequest) -> NluResult: ...


def recognize_days(request: NluRequest) -> DayEvidence | None:
    if (
        request.question_timeframe != "past_14_days"
        or request.clarification
        != ClarificationContext(request.item_id, "frequency_in_past_14_days")
    ):
        return None
    match = _DAYS.fullmatch(request.text.strip().casefold().rstrip(".!?").rstrip())
    if match is None:
        return None
    approximation, number = match.groups()
    count = int(number) if number.isdecimal() else _DAY_WORDS.index(number)
    return DayEvidence(count, approximation is not None) if count <= 14 else None


class RuleProvider:
    def predict(self, request: NluRequest) -> NluResult:
        result = extract(request.item_id, request.text)
        if (
            request.clarification is not None
            and request.clarification.item_id != request.item_id
        ):
            result.update(
                frequency_candidate=None, symptom_present=None, ambiguity="off_topic"
            )
        elif (
            result["timeframe"] == "missing"
            and request.question_timeframe == "past_14_days"
        ):
            scoped = extract(request.item_id, "過去兩週" + request.text.strip())
            if scoped["frequency_candidate"] is not None:
                result = scoped
        result["model_version"] = "context-rule-zh-hant-v1"
        return result
