"""Reproducible English TweetEval experiment; no depression labels."""

import argparse
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter

import joblib
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.metrics import f1_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

LABELS = ["negative", "neutral", "positive"]


def load_split(root, split):
    texts = (root / f"{split}_text.txt").read_text().splitlines()
    labels = np.array(
        [int(x) for x in (root / f"{split}_labels.txt").read_text().splitlines()]
    )
    if len(texts) != len(labels) or not len(texts) or not set(labels) <= {0, 1, 2}:
        raise ValueError("Invalid TweetEval split")
    return texts, labels


def metrics(gold, predicted):
    return {
        "n": len(gold),
        "accuracy": float(accuracy_score(gold, predicted)),
        "macro_f1": float(f1_score(gold, predicted, labels=[0, 1, 2], average="macro")),
        "macro_recall": float(
            recall_score(gold, predicted, labels=[0, 1, 2], average="macro")
        ),
        "confusion_matrix": confusion_matrix(
            gold, predicted, labels=[0, 1, 2]
        ).tolist(),
        "per_class": classification_report(
            gold,
            predicted,
            labels=[0, 1, 2],
            target_names=LABELS,
            output_dict=True,
            zero_division=0,
        ),
    }


def run(data, output):
    if output.exists():
        raise ValueError("Use a new output directory")
    output.mkdir(parents=True)
    train_x, train_y = load_split(data, "train")
    val_x, val_y = load_split(data, "val")
    test_x, test_y = load_split(data, "test")
    trials, selected = [], {}
    for name in ("logistic_regression", "linear_svm"):
        best = -1
        for c in (0.1, 1.0, 10.0):
            classifier = (
                LogisticRegression(C=c, max_iter=1500, random_state=42)
                if name == "logistic_regression"
                else LinearSVC(C=c, random_state=42)
            )
            model = Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            ngram_range=(1, 2),
                            min_df=2,
                            max_features=50000,
                            sublinear_tf=True,
                        ),
                    ),
                    ("classifier", classifier),
                ]
            )
            started = perf_counter()
            model.fit(train_x, train_y)
            score = f1_score(
                val_y, model.predict(val_x), labels=[0, 1, 2], average="macro"
            )
            trials.append(
                {
                    "model": name,
                    "C": c,
                    "validation_macro_f1": float(score),
                    "fit_and_validation_seconds": perf_counter() - started,
                }
            )
            if score > best:
                best = score
                selected[name] = (model, c, float(score))
    # Freeze model selection on validation BEFORE making test predictions.
    winner = max(selected, key=lambda name: selected[name][2])
    (output / "selection.json").write_text(
        json.dumps(
            {
                "trials": trials,
                "winner": winner,
                "protocol": "Train only; validation selects C and model; no train+validation refit.",
            },
            indent=2,
        )
    )
    dummy = DummyClassifier(strategy="most_frequent").fit(
        np.zeros((len(train_y), 1)), train_y
    )
    predictions = {"majority": dummy.predict(np.zeros((len(test_y), 1)))}
    for name, (model, _, _) in selected.items():
        predictions[name] = model.predict(test_x)
    results = {name: metrics(test_y, pred) for name, pred in predictions.items()}
    # Paired nonparametric bootstrap on held-out rows; selection remains fixed.
    rng = np.random.default_rng(42)
    diffs = []
    for _ in range(500):
        indexes = rng.integers(0, len(test_y), len(test_y))
        a = f1_score(
            test_y[indexes],
            predictions[winner][indexes],
            labels=[0, 1, 2],
            average="macro",
        )
        b = f1_score(
            test_y[indexes],
            predictions["majority"][indexes],
            labels=[0, 1, 2],
            average="macro",
        )
        diffs.append(a - b)

    def digest(text):
        return hashlib.sha256(text.strip().casefold().encode()).hexdigest()

    sets = [set(map(digest, x)) for x in (train_x, val_x, test_x)]
    metadata = {
        "language": "English",
        "task": "general sentiment, not depression prediction",
        "train_n": len(train_y),
        "validation_n": len(val_y),
        "test_n": len(test_y),
        "class_counts": {
            name: np.bincount(y, minlength=3).tolist()
            for name, y in (("train", train_y), ("validation", val_y), ("test", test_y))
        },
        "selected_model": winner,
        "selected_C": selected[winner][1],
        "validation_macro_f1": selected[winner][2],
        "exact_normalized_overlap_unique": {
            "train_val": len(sets[0] & sets[1]),
            "train_test": len(sets[0] & sets[2]),
            "val_test": len(sets[1] & sets[2]),
        },
        "bootstrap": {
            "comparison": f"{winner} minus majority macro-F1",
            "resamples": 500,
            "seed": 42,
            "percentile_95_ci": np.quantile(diffs, [0.025, 0.975]).tolist(),
            "limitation": "Tweet-level sampling; authors/topics may be dependent.",
        },
        "python": platform.python_version(),
        "platform": platform.platform(),
        "source_manifest": json.loads((data / "manifest.json").read_text()),
    }
    clean = np.array([digest(t) not in sets[0] | sets[1] for t in test_x])
    metadata["unseen_exact_text_sensitivity"] = metrics(
        test_y[clean], predictions[winner][clean]
    )
    (output / "metrics.json").write_text(
        json.dumps({"metadata": metadata, "results": results}, indent=2)
    )
    import csv

    with (output / "predictions.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["test_row", "text_sha256", "gold", *predictions])
        for i, text in enumerate(test_x):
            writer.writerow(
                [
                    i,
                    digest(text),
                    int(test_y[i]),
                    *[int(pred[i]) for pred in predictions.values()],
                ]
            )
    errors = [i for i, (a, b) in enumerate(zip(test_y, predictions[winner])) if a != b]
    (output / "error_indices.json").write_text(json.dumps(errors[:30]))
    joblib.dump(selected[winner][0], output / "sentiment_model.joblib")
    print(
        json.dumps(
            {
                "selected": winner,
                "results": {
                    k: {n: v[n] for n in ("accuracy", "macro_f1")}
                    for k, v in results.items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.data, args.output)
