"""Context-aware candidate interface with locally validated R1 intervals."""

import re
from dataclasses import dataclass, field
from typing import Literal, Protocol

from rule_nlu import extract
from schemas import LocalDayResult, NluResult
from research.day_mapping import map_days

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
_ZH_NUMBERS = dict(
    zip(
        (
            "零",
            "一",
            "二",
            "三",
            "四",
            "五",
            "六",
            "七",
            "八",
            "九",
            "十",
            "十一",
            "十二",
            "十三",
            "十四",
        ),
        range(15),
    )
)
_NUMBER = (
    r"(?:\d{1,2}|"
    + "|".join(_DAY_WORDS)
    + "|"
    + "|".join(sorted(_ZH_NUMBERS, key=len, reverse=True))
    + ")"
)
_INTERVAL = re.compile(
    r"(?:(around|about|大約|約)\s*)?("
    + _NUMBER
    + r")(?:\s*(?:-|–|至|到|to)\s*("
    + _NUMBER
    + r"))?\s*(?:days?|天|日)"
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
    upper: int | None = None

    @property
    def interval(self):
        if self.upper is not None:
            return self.count, self.upper
        margin = int(self.approximate)
        return max(0, self.count - margin), min(14, self.count + margin)


class NLUProvider(Protocol):
    def predict(self, request: NluRequest) -> NluResult: ...


def recognize_days(request: NluRequest) -> DayEvidence | None:
    if (
        request.question_timeframe != "past_14_days"
        or request.clarification
        != ClarificationContext(request.item_id, "frequency_in_past_14_days")
    ):
        return None
    match = _INTERVAL.fullmatch(
        request.text.strip().casefold().rstrip(".!?。！").rstrip()
    )
    if match is None:
        return None
    approximation, number, endpoint = match.groups()

    def number_value(token):
        if token.isdecimal():
            return int(token)
        return _ZH_NUMBERS[token] if token in _ZH_NUMBERS else _DAY_WORDS.index(token)

    count = number_value(number)
    upper = number_value(endpoint) if endpoint is not None else None
    if count > 14 or upper is not None and not count <= upper <= 14:
        return None
    return DayEvidence(count, approximation is not None, upper)


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
        elif (days := recognize_days(request)) is not None:
            lower, upper = days.interval
            value = map_days(lower, upper)
            result.update(
                timeframe="past_14_days",
                frequency_candidate=value,
                symptom_present=False if upper == 0 else True if lower > 0 else None,
                negation="clear" if upper == 0 else "none",
                ambiguity="none" if value is not None else "ambiguous_frequency",
            )
            result = LocalDayResult(result, days.interval)
        elif (
            result["timeframe"] == "missing"
            and request.question_timeframe == "past_14_days"
        ):
            scoped = extract(request.item_id, "過去兩週" + request.text.strip())
            if scoped["frequency_candidate"] is not None:
                result = scoped
        result["model_version"] = "context-rule-r1-v2"
        return result
