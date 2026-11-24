"""Numerical helpers for synthetic checks and frozen research runs."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class RiskPoint:
    threshold: float
    coverage: float
    risk: float | None


def risk_coverage(records, thresholds):
    """Records are (confidence, correct, eligible) from one provider/version."""
    rows = tuple(records)
    if not rows:
        raise ValueError("Risk–coverage requires at least one labelled row.")
    for confidence, correct, eligible in rows:
        if type(correct) is not bool or type(eligible) is not bool:
            raise ValueError("Correctness and hard-rule eligibility must be boolean.")
        if confidence is not None and (
            type(confidence) not in {int, float} or not 0 <= confidence <= 1
        ):
            raise ValueError("Invalid confidence.")
    points = []
    for threshold in thresholds:
        if type(threshold) not in {int, float} or not 0 <= threshold <= 1:
            raise ValueError("Invalid threshold.")
        accepted = [
            correct
            for confidence, correct, eligible in rows
            if eligible and confidence is not None and confidence >= threshold
        ]
        risk = 1 - sum(accepted) / len(accepted) if accepted else None
        points.append(RiskPoint(threshold, len(accepted) / len(rows), risk))
    return points


def select_threshold(points, baseline_risk):
    if baseline_risk is None:
        return None
    return max(
        (p for p in points if p.risk is not None and p.risk <= baseline_risk),
        key=lambda p: (p.coverage, p.threshold),
        default=None,
    )


def observed_aurc(points):
    observed = sorted({(p.coverage, p.risk) for p in points if p.risk is not None})
    if len(observed) < 2:
        return None
    area = sum(
        (right - left) * (before + after) / 2
        for (left, before), (right, after) in zip(observed, observed[1:])
    )
    return area, observed[0][0], observed[-1][0]


def pareto_front(rows):
    """Metrics are (accuracy, risk, latency, cost, turns) from like-for-like runs."""
    candidates = {}
    excluded = []
    for name, metrics in rows.items():
        if len(metrics) != 5:
            raise ValueError("Expected five metrics.")
        if any(value is None for value in metrics):
            excluded.append(name)
            continue
        if (
            any(
                type(value) not in {int, float} or not isfinite(value) or value < 0
                for value in metrics
            )
            or metrics[0] > 1
            or metrics[1] > 1
        ):
            raise ValueError("Invalid metric.")
        accuracy, *minimized = metrics
        candidates[name] = (-accuracy, *minimized)
    front = [
        name
        for name, metrics in candidates.items()
        if not any(
            other != metrics and all(a <= b for a, b in zip(other, metrics))
            for other in candidates.values()
        )
    ]
    return sorted(front), sorted(excluded)
