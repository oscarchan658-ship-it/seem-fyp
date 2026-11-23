from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfirmedAnswer:
    item_id: int
    value: int


@dataclass(frozen=True)
class Phq8Result:
    total: int
    band: str


_BANDS = ("0–4", "5–9", "10–14", "15–19", "20–24")


def score_phq8(confirmed: Sequence[ConfirmedAnswer]) -> Phq8Result:
    """Score eight explicitly confirmed PHQ-8 responses."""
    if not isinstance(confirmed, Sequence) or len(confirmed) != 8:
        raise ValueError("Exactly eight confirmed answers are required.")

    seen_items = set()
    total = 0
    for answer in confirmed:
        if not isinstance(answer, ConfirmedAnswer):
            raise ValueError("Each answer must be confirmed.")
        if type(answer.item_id) is not int or not 1 <= answer.item_id <= 8:
            raise ValueError("item_id must be an integer from 1 to 8.")
        if answer.item_id in seen_items:
            raise ValueError("Duplicate item_id.")
        if type(answer.value) is not int or not 0 <= answer.value <= 3:
            raise ValueError("Answer value must be an integer from 0 to 3.")
        seen_items.add(answer.item_id)
        total += answer.value

    return Phq8Result(total, _BANDS[total // 5])
