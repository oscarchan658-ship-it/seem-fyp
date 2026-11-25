"""Fixed-denominator E2a/E2b metrics and Validation-only threshold freezing."""

from math import isfinite

from research.evaluation import risk_coverage, select_threshold


def metrics(rows):
    rows = list(rows)
    for row in rows:
        gold, prediction = row["gold_frequency"], row["prediction"]
        if gold != "unresolved" and (type(gold) is not int or not 0 <= gold <= 3):
            raise ValueError("Invalid Gold.")
        if prediction is not None and (
            type(prediction) is not int or not 0 <= prediction <= 3
        ):
            raise ValueError("Invalid prediction.")
    total = len(rows)
    accepted = [row for row in rows if row["prediction"] is not None]
    resolved = [row for row in rows if row["gold_frequency"] != "unresolved"]
    unresolved = [row for row in rows if row["gold_frequency"] == "unresolved"]
    correct = sum(row["prediction"] == row["gold_frequency"] for row in accepted)
    support, f1 = [], []
    for value in range(4):
        tp = sum(row["prediction"] == value == row["gold_frequency"] for row in rows)
        fp = sum(
            row["prediction"] == value and row["gold_frequency"] != value
            for row in rows
        )
        fn = sum(
            row["gold_frequency"] == value and row["prediction"] != value
            for row in rows
        )
        support.append(tp + fn)
        f1.append(2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 0)
    return dict(
        total=total,
        accepted=len(accepted),
        resolved_gold=len(resolved),
        unresolved_gold=len(unresolved),
        frequency_accuracy=correct / len(resolved) if resolved else None,
        macro_f1=sum(f1) / 4 if total else None,
        class_f1=f1,
        class_support=support,
        abstention_rate=(total - len(accepted)) / total if total else None,
        coverage=len(accepted) / total if total else None,
        gold_unresolved_rate=len(unresolved) / total if total else None,
        unresolved_false_accept_rate=sum(
            row["prediction"] is not None for row in unresolved
        )
        / len(unresolved)
        if unresolved
        else None,
        selective_risk=(len(accepted) - correct) / len(accepted) if accepted else None,
        system_failure_rate=sum(row.get("error") is not None for row in rows) / total
        if total
        else None,
    )


def freeze_threshold(rows):
    rows = list(rows)
    summary = metrics(rows)
    signals = [row.get("confidence") for row in rows]
    if any(
        value is not None
        and (
            type(value) not in {int, float}
            or not isfinite(value)
            or not 0 <= value <= 1
        )
        for value in signals
    ):
        raise ValueError("Invalid confidence.")
    thresholds = sorted({0, 1, *(value for value in signals if value is not None)})
    points = (
        risk_coverage(
            [
                (
                    row.get("confidence"),
                    row["prediction"] == row["gold_frequency"],
                    row["prediction"] is not None,
                )
                for row in rows
            ],
            thresholds,
        )
        if rows
        else []
    )
    choice = select_threshold(points, summary["selective_risk"])
    return dict(
        status="FROZEN" if choice is not None else "NOT RUN",
        baseline_risk=summary["selective_risk"],
        baseline_accepted=summary["accepted"],
        baseline_wrong=sum(
            row["prediction"] is not None and row["prediction"] != row["gold_frequency"]
            for row in rows
        ),
        threshold=choice.threshold if choice else None,
        grid=thresholds,
        points=[
            dict(threshold=p.threshold, coverage=p.coverage, risk=p.risk)
            for p in points
        ],
    )
