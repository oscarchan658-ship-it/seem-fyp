import re

from schemas import NluResult

MODEL_VERSION = "synthetic-rule-zh-hant-v2"
_FREQUENCIES = ("完全沒有", "有幾天", "超過一半的日子", "幾乎每天")
_WINDOW = re.compile(r"^(過去兩週|過去兩星期|過去14天)\s*[，,：:]?\s*")


def extract(item_id: int, text: str) -> NluResult:
    """Parse the small set of synthetic replies scoped to the current item."""
    text = text.strip().rstrip("。.!！").rstrip()
    window = _WINDOW.match(text)
    timeframe = (
        "past_14_days" if window else "other" if text.startswith("上週") else "missing"
    )
    out: NluResult = {
        "item_id": item_id,
        "frequency_candidate": None,
        "timeframe": timeframe,
        "symptom_present": None,
        "negation": "none",
        "ambiguity": "uncertain",
        "model_version": MODEL_VERSION,
    }
    if not window:
        return out

    answer = text[window.end() :]
    mentions = [frequency for frequency in _FREQUENCIES if frequency in answer]
    if len(mentions) > 1:
        out["ambiguity"] = "contradiction"
        return out
    if "有時" in answer:
        out["ambiguity"] = "ambiguous_frequency"
        return out
    if answer.startswith(("並非", "不是")):
        out["negation"] = "unclear"
        return out
    if answer.startswith("不確定"):
        return out
    value = next(
        (
            index
            for index, frequency in enumerate(_FREQUENCIES)
            if answer
            in (frequency, frequency + ("此症狀" if index == 0 else "出現此症狀"))
        ),
        None,
    )
    if value is None:
        out["ambiguity"] = "off_topic"
        return out

    out.update(frequency_candidate=value, symptom_present=value > 0, ambiguity="none")
    out["negation"] = "clear" if value == 0 else "none"
    return out
