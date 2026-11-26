"""Display locally recognized day evidence without changing scoring."""

OPTIONS = ("完全沒有", "有幾天", "超過一半的日子", "幾乎每天")


def describe_answer(state, item):
    value = state.provisional_answers[item]
    interval = state.day_intervals.get(item)
    if interval is None:
        return OPTIONS[value]
    low, high = interval
    days = str(low) if low == high else f"{low}–{high}"
    return f"過去兩週 {days} 天 · PHQ-8 Days 轉換候選 {value} 分（R1）"
