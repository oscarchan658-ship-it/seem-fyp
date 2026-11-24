"""Paired group resampling and annotation agreement for frozen evaluations."""

import random


def paired_bootstrap(groups, metric, *, repetitions=2000, seed=42):
    """Each group holds aligned (gold, prediction_a, prediction_b) rows."""
    if not groups or type(repetitions) is not int or repetitions < 2:
        raise ValueError("Bootstrap requires groups and at least two draws.")
    clusters = tuple(tuple(rows) for rows in groups.values())
    if any(not group for group in clusters):
        raise ValueError("Empty bootstrap group.")

    def difference(draw):
        gold, first, second = zip(*(row for group in draw for row in group))
        a, b = metric(gold, first), metric(gold, second)
        return None if a is None or b is None else a - b

    rng = random.Random(seed)
    values = [
        difference(rng.choices(clusters, k=len(clusters))) for _ in range(repetitions)
    ]
    valid = sorted(value for value in values if value is not None)
    bounds = (
        None
        if not valid
        else (
            valid[int((len(valid) - 1) * 0.025)],
            valid[int((len(valid) - 1) * 0.975)],
        )
    )
    return difference(clusters), bounds, repetitions - len(valid)


def cohens_kappa(left, right, labels, *, ordered=False):
    if (
        not left
        or len(left) != len(right)
        or len(labels) < 2
        or len(set(labels)) != len(labels)
    ):
        raise ValueError("Invalid agreement sample or labels.")
    indices = {label: index for index, label in enumerate(labels)}
    if not set(left).union(right) <= indices.keys():
        raise ValueError("Unknown annotation label.")

    def disagreement(a, b):
        return (
            ((indices[a] - indices[b]) / (len(labels) - 1)) ** 2 if ordered else a != b
        )

    size = len(left)
    observed = sum(disagreement(a, b) for a, b in zip(left, right)) / size
    expected = (
        sum(
            disagreement(a, b) * left.count(a) * right.count(b)
            for a in labels
            for b in labels
        )
        / size**2
    )
    return None if not expected else 1 - observed / expected
