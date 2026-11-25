"""Deterministic group-aware Development split with explicit coverage diagnostics."""

import random
from collections import Counter, defaultdict


def split_coverage(rows, categories, *, seed=42, fraction=0.25):
    if (
        not rows
        or not 0 < fraction < 1
        or len({row["case_id"] for row in rows}) != len(rows)
    ):
        raise ValueError("Expected unique Development cases and a valid fraction.")
    if set(categories) != {row["case_id"] for row in rows}:
        raise ValueError("Coverage categories must match Development IDs exactly.")
    groups = defaultdict(list)
    for row in sorted(rows, key=lambda row: row["case_id"]):
        groups[row["group_id"]].append(row)
    if len(groups) < 2:
        raise ValueError("Train and validation need independent groups.")
    names = sorted(groups)
    random.Random(seed).shuffle(names)

    def labels(row):
        return (
            ("item", row["item_id"]),
            ("gold", str(row["gold_frequency"])),
            ("category", categories[row["case_id"]]),
        )

    group_counts = {
        name: Counter(label for row in group for label in labels(row))
        for name, group in groups.items()
    }
    total = sum(group_counts.values(), Counter())
    occurrences = Counter(label for counts in group_counts.values() for label in counts)
    repeated = {label for label, count in occurrences.items() if count >= 2}
    target = max(1, round(len(rows) * fraction))

    def objective(selected):
        if not selected or len(selected) == len(names):
            return (float("inf"),)
        validation = sum((group_counts[name] for name in selected), Counter())
        train = total - validation
        missed = sum(
            label not in validation or label not in train for label in repeated
        )
        singleton_moved = sum(
            label not in train for label, count in occurrences.items() if count == 1
        )
        size = sum(len(groups[name]) for name in selected)
        imbalance = sum(
            abs(validation[label] / total[label] - fraction) for label in total
        )
        return missed, singleton_moved, abs(size - target), imbalance

    selected = {min(names, key=lambda name: objective({name}))}
    while True:
        best, best_score = selected, objective(selected)
        options = [
            {*selected, name} if name not in selected else selected - {name}
            for name in names
        ]
        options.extend(
            (selected - {left}) | {right}
            for left in names
            if left in selected
            for right in names
            if right not in selected
        )
        for option in options:
            score = objective(option)
            if score < best_score:
                best, best_score = option, score
        if best == selected:
            break
        selected = best
    train = [
        row
        for row in sorted(rows, key=lambda row: row["case_id"])
        if row["group_id"] not in selected
    ]
    validation = [
        row
        for row in sorted(rows, key=lambda row: row["case_id"])
        if row["group_id"] in selected
    ]
    train_labels, val_labels = (
        set(label for row in train for label in labels(row)),
        set(label for row in validation for label in labels(row)),
    )
    missing = [
        dict(
            dimension=label[0],
            value=label[1],
            train=label in train_labels,
            validation=label in val_labels,
            independent_groups=occurrences[label],
        )
        for label in sorted(total)
        if label not in train_labels or label not in val_labels
    ]
    review = any(
        row["dimension"] in {"item", "gold"} and row["independent_groups"] >= 2
        for row in missing
    )
    return (
        train,
        validation,
        dict(
            status="SPLIT_REVIEW_REQUIRED" if review else "READY",
            seed=seed,
            target_cases=target,
            train_cases=len(train),
            validation_cases=len(validation),
            train_groups=len(groups) - len(selected),
            validation_groups=len(selected),
            missing_coverage=missing,
        ),
    )
