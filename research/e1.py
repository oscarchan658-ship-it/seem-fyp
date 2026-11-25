"""Controlled S/N/F logistic-regression comparison from approved numeric features."""

import argparse
import hashlib
import json
import platform
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from research.annotation import _write_csv
from research.statistics import paired_bootstrap

GRID = [0.01, 0.1, 1, 10, 100]


def _metrics(gold, scores):
    predicted = [int(value >= 0.5) for value in scores]
    return dict(
        auroc=float(roc_auc_score(gold, scores)) if len(set(gold)) == 2 else None,
        precision=float(precision_score(gold, predicted, zero_division=0)),
        recall=float(recall_score(gold, predicted, zero_division=0)),
        macro_f1=float(
            f1_score(gold, predicted, labels=[0, 1], average="macro", zero_division=0)
        ),
        confusion=confusion_matrix(gold, predicted, labels=[0, 1]).tolist(),
    )


def run(rows, config, output, *, repetitions=2000):
    if (
        config.get("mode") not in {"synthetic", "empirical"}
        or not config.get("target_definition")
        or not config.get("dataset_version")
    ):
        raise ValueError(
            "Evidence mode, target definition and dataset version are required."
        )
    if config["mode"] == "empirical" and not config.get("dataset_authorized"):
        raise ValueError("Dataset A authorization is required.")
    participants, ids, duplicate_text = {}, set(), {}
    sizes = None
    for row in rows:
        participant, case, split, target = (
            row["participant_id"],
            row["case_id"],
            row["split"],
            row["target"],
        )
        if (
            not participant
            or case in ids
            or split not in {"train", "validation", "test"}
            or type(target) is not int
            or target not in {0, 1}
        ):
            raise ValueError("Invalid E1 case.")
        ids.add(case)
        if participants.setdefault(participant, (split, target)) != (split, target):
            raise ValueError(
                "A participant crosses splits or has inconsistent targets."
            )
        fingerprint = row.get("text_fingerprint")
        if fingerprint and duplicate_text.setdefault(fingerprint, split) != split:
            raise ValueError("Duplicate text crosses splits.")
        dimensions = tuple(
            len(row[key]) for key in ("sentiment_features", "context_features")
        )
        if not all(dimensions) or sizes is not None and dimensions != sizes:
            raise ValueError("Inconsistent feature dimensions.")
        sizes = dimensions
        if any(
            type(value) not in {int, float} or not np.isfinite(value)
            for key in ("sentiment_features", "context_features")
            for value in row[key]
        ):
            raise ValueError("Nonfinite or nonnumeric features.")
        if type(row["divergence"]) is not bool:
            raise ValueError("Divergence must be independently labelled.")
    sets = {
        split: [row for row in rows if row["split"] == split]
        for split in ("train", "validation", "test")
    }
    if any({row["target"] for row in group} != {0, 1} for group in sets.values()):
        raise ValueError("Each split must contain both target classes.")
    output.mkdir(parents=True)
    models, predictions, metrics_rows, divergence_rows = {}, {}, [], []
    for arm, feature_keys in (
        ("S", ("sentiment_features",)),
        ("N", ("context_features",)),
        ("F", ("context_features", "sentiment_features")),
    ):

        def features(group):
            return [sum((row[key] for key in feature_keys), []) for row in group]

        best_model, best_score, best_c = None, -1, None
        for c in GRID:
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    C=c,
                    solver="liblinear",
                    random_state=42,
                    class_weight=None,
                    tol=1e-4,
                    max_iter=1000,
                ),
            )
            model.fit(features(sets["train"]), [row["target"] for row in sets["train"]])
            validation_scores = model.predict_proba(features(sets["validation"]))[:, 1]
            score = _metrics(
                [row["target"] for row in sets["validation"]], validation_scores
            )["macro_f1"]
            if score > best_score:
                best_model, best_score, best_c = model, score, c
        scores = best_model.predict_proba(features(sets["test"]))[:, 1]
        predictions[arm] = dict(
            zip((row["case_id"] for row in sets["test"]), map(float, scores))
        )
        records = [
            dict(
                case_id=row["case_id"],
                participant_id=row["participant_id"],
                target=row["target"],
                score=float(score),
                prediction=int(score >= 0.5),
                divergence=row["divergence"],
            )
            for row, score in zip(sets["test"], scores)
        ]
        _write_csv(
            output / f"predictions_{arm.lower()}.csv", tuple(records[0]), records
        )
        values = _metrics([row["target"] for row in sets["test"]], scores)
        metrics_rows.append(dict(arm=arm, **values))
        for divergence in (False, True):
            group = [row for row in records if row["divergence"] == divergence]
            divergence_rows.append(
                dict(
                    arm=arm,
                    divergence=divergence,
                    count=len(group),
                    errors=sum(row["target"] != row["prediction"] for row in group),
                    macro_f1=_metrics(
                        [row["target"] for row in group],
                        [row["score"] for row in group],
                    )["macro_f1"]
                    if group
                    else None,
                )
            )
        models[arm] = dict(
            family="L2 logistic regression",
            solver="liblinear",
            grid=GRID,
            tuning_trials=5,
            selected_c=best_c,
            validation_macro_f1=best_score,
            seed=42,
            threshold=0.5,
            class_weight=None,
            tol=1e-4,
            max_iter=1000,
        )
    grouped = defaultdict(list)
    for row in sets["test"]:
        key = row["case_id"]
        grouped[row["participant_id"]].append(
            (row["target"], predictions["F"][key], predictions["N"][key])
        )
    difference, bounds, invalid = paired_bootstrap(
        grouped,
        lambda gold, scores: _metrics(gold, scores)["macro_f1"],
        repetitions=repetitions,
        seed=42,
    )
    _write_csv(
        output / "metrics.csv",
        tuple(metrics_rows[0]),
        (
            {
                key: json.dumps(value) if isinstance(value, list) else value
                for key, value in row.items()
            }
            for row in metrics_rows
        ),
    )
    _write_csv(
        output / "bootstrap_ci.csv",
        ("comparison", "difference", "lower", "upper", "draws", "invalid_draws"),
        [
            dict(
                comparison="F-N",
                difference=difference,
                lower=bounds[0] if bounds else None,
                upper=bounds[1] if bounds else None,
                draws=repetitions,
                invalid_draws=invalid,
            )
        ],
    )
    _write_csv(
        output / "divergence_analysis.csv", tuple(divergence_rows[0]), divergence_rows
    )
    manifest = dict(
        config=config,
        models=models,
        primary_comparison="F-N",
        empirical_e1="NOT RUN" if config["mode"] == "synthetic" else "RUN",
        python=platform.python_version(),
        participants=len(participants),
        split_counts={split: len(group) for split, group in sets.items()},
        source_sha256=hashlib.sha256(
            json.dumps(rows, sort_keys=True).encode()
        ).hexdigest(),
        files={
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in output.glob("*.csv")
        },
    )
    (output / "dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("features", type=Path)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.features.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(
        json.dumps(
            run(rows, json.loads(args.config.read_text(encoding="utf-8")), args.output),
            indent=2,
        )
    )
