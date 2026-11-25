"""R1 v1: exact day intervals and conservative approximate-day mapping."""


def map_days(lower: int, upper: int) -> int | None:
    if (
        type(lower) is not int
        or type(upper) is not int
        or not 0 <= lower <= upper <= 14
    ):
        raise ValueError("Expected an integer interval within 0–14 days.")

    def category(days):
        return sum(days >= boundary for boundary in (2, 7, 12))

    low, high = category(lower), category(upper)
    return low if low == high else None
