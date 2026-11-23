"""Check E1 plumbing with fixed synthetic scores, without an empirical model run."""

import json
from itertools import groupby

_ARMS = ("S", "N", "F")


def _metrics(gold, scores):
    confusion = [[0, 0], [0, 0]]
    observations = []
    for case_id, truth in gold.items():
        score = scores[case_id]
        if type(score) not in (int, float) or not 0 <= score <= 1:
            raise ValueError(f"Invalid synthetic score for {case_id}.")
        observations.append((score, truth))
        confusion[truth][int(score >= 0.5)] += 1
    (tn, fp), (fn, tp) = confusion

    negatives_seen = concordance = 0
    for _, group in groupby(
        sorted(observations), key=lambda observation: observation[0]
    ):
        labels = [truth for _, truth in group]
        positives = sum(labels)
        negatives = len(labels) - positives
        concordance += positives * (negatives_seen + 0.5 * negatives)
        negatives_seen += negatives
    return {
        "confusion": confusion,
        "auroc": concordance / ((tp + fn) * (tn + fp)),
        "macro_f1": (tn / (2 * tn + fp + fn)) + (tp / (2 * tp + fp + fn)),
        "recall": tp / (tp + fn),
    }


def evaluate_smoke(gold, arms):
    if set(arms) != set(_ARMS):
        raise ValueError("Expected S, N and F.")
    if any(type(label) is not int for label in gold.values()) or set(gold.values()) != {
        0,
        1,
    }:
        raise ValueError("Synthetic gold must contain both binary classes.")
    if any(scores.keys() != gold.keys() for scores in arms.values()):
        raise ValueError("All arms must use the same test case IDs.")
    return {arm: _metrics(gold, arms[arm]) for arm in _ARMS}


def run_smoke():
    gold = {"fixture-1": 0, "fixture-2": 1, "fixture-3": 0, "fixture-4": 1}
    sentiment = dict(zip(gold, (0.1, 0.7, 0.6, 0.9), strict=True))
    context = dict(zip(gold, (0.2, 0.9, 0.1, 0.4), strict=True))
    fusion = {key: (sentiment[key] + context[key]) / 2 for key in gold}
    evaluated = evaluate_smoke(gold, {"S": sentiment, "N": context, "F": fusion})
    return {
        "mode": "Engineering Smoke Test",
        "arms_checked": list(evaluated),
        "cases_checked_per_arm": len(gold),
        "empirical_e1": "NOT RUN",
    }


if __name__ == "__main__":
    print(json.dumps(run_smoke(), indent=2))
