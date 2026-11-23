import pytest

from phq8_engine import ConfirmedAnswer, Phq8Result, score_phq8


def confirmed_answers(values):
    return tuple(
        ConfirmedAnswer(item_id, value) for item_id, value in enumerate(values, 1)
    )


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        pytest.param([0] * 8, Phq8Result(0, "0–4"), id="T01-all-zero"),
        pytest.param([3] * 8, Phq8Result(24, "20–24"), id="T02-all-three"),
        pytest.param([0, 1, 2, 3] * 2, Phq8Result(12, "10–14"), id="T03-mixed"),
    ],
)
def test_scores_confirmed_answers(values, expected):
    assert score_phq8(confirmed_answers(values)[::-1]) == expected


@pytest.mark.parametrize(
    "invalid_value",
    [-1, 4, 1.0, "1", True, None],
)
def test_t04_rejects_invalid_values(invalid_value):
    with pytest.raises(ValueError, match="value"):
        score_phq8(confirmed_answers([0] * 7 + [invalid_value]))


@pytest.mark.parametrize("invalid_id", [0, 9, 8.0, "8", True, None])
def test_t04_rejects_invalid_item_ids(invalid_id):
    answers = confirmed_answers([0] * 7) + (ConfirmedAnswer(invalid_id, 0),)

    with pytest.raises(ValueError, match="item_id"):
        score_phq8(answers)


@pytest.mark.parametrize("count", [7, 9])
def test_t05_requires_exactly_eight_answers(count):
    with pytest.raises(ValueError, match="eight"):
        score_phq8(confirmed_answers([0] * count))


def test_t06_rejects_duplicate_answer_in_place_of_missing_item():
    answers = confirmed_answers([0] * 7) + (ConfirmedAnswer(7, 0),)

    with pytest.raises(ValueError, match="Duplicate item_id"):
        score_phq8(answers)


@pytest.mark.parametrize(
    ("total", "band"),
    [
        (0, "0–4"),
        (4, "0–4"),
        (5, "5–9"),
        (9, "5–9"),
        (10, "10–14"),
        (14, "10–14"),
        (15, "15–19"),
        (19, "15–19"),
        (20, "20–24"),
        (24, "20–24"),
    ],
)
def test_t25_classifies_band_endpoints(total, band):
    values = [min(3, max(0, total - 3 * index)) for index in range(8)]

    assert score_phq8(confirmed_answers(values)) == Phq8Result(total, band)


@pytest.mark.parametrize(
    "answers",
    [
        (0,) * 8,
        confirmed_answers([0] * 7) + (0,),
        {item_id: 0 for item_id in range(1, 9)},
    ],
    ids=["all-provisional", "one-provisional", "provisional-map"],
)
def test_t25_rejects_unconfirmed_answers(answers):
    with pytest.raises(ValueError, match="confirmed"):
        score_phq8(answers)
