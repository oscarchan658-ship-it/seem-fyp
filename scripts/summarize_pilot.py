import json
import collections
import argparse
from pathlib import Path
import numpy as np
import joblib
from sklearn.metrics import f1_score

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(
    description="Summarize the fixed 48-case authored pilot without API calls"
)
parser.add_argument(
    "--folder", type=Path, default=root / "results/terra-sentiment-20261126"
)
parser.add_argument(
    "--model",
    type=Path,
    default=root / "results/tweeteval-20261126/sentiment_model.joblib",
)
args = parser.parse_args()
folder = args.folder
rows = [json.loads(x) for x in (folder / "predictions.jsonl").read_text().splitlines()]
summary = {"n": len(rows), "groups": {}, "errors": []}
for language in ["en", "zh-Hant"]:
    r = [x for x in rows if x["language"] == language]
    valid = [x for x in r if x["predicted"] in ["negative", "neutral", "positive"]]
    summary["groups"][language] = {
        "n": len(r),
        "valid": len(valid),
        "correct": sum(x["predicted"] == x["expected"] for x in r),
        "macro_f1_valid": f1_score(
            [x["expected"] for x in valid],
            [x["predicted"] for x in valid],
            labels=["negative", "neutral", "positive"],
            average="macro",
        ),
    }
model = joblib.load(args.model)
en = [x for x in rows if x["language"] == "en"]
labels = ["negative", "neutral", "positive"]
pred = [labels[int(x)] for x in model.predict([x["text"] for x in en])]
summary["local_english"] = {
    "n": 24,
    "correct": sum(p == x["expected"] for p, x in zip(pred, en)),
    "macro_f1": f1_score(
        [x["expected"] for x in en], pred, labels=labels, average="macro"
    ),
}
(folder / "local_english_predictions.json").write_text(
    json.dumps(
        [
            {"case_id": x["case_id"], "expected": x["expected"], "predicted": p}
            for x, p in zip(en, pred)
        ],
        indent=2,
    )
)
pairs = collections.defaultdict(list)
for x in rows:
    pairs[x["pair_id"]].append(x["predicted"])
summary["translation_agreement"] = sum(
    len(p) == 2 and p[0] is not None and p[0] == p[1] for p in pairs.values()
)
summary["latency_seconds"] = {
    k: float(v)
    for k, v in zip(
        ["median", "p95", "max"],
        [
            np.median([x["seconds"] for x in rows if "seconds" in x]),
            np.percentile([x["seconds"] for x in rows if "seconds" in x], 95),
            max(x["seconds"] for x in rows if "seconds" in x),
        ],
    )
}
summary["reported_tokens"] = {
    k: sum((x.get("usage") or {}).get(k, 0) for x in rows)
    for k in ["input_tokens", "output_tokens", "total_tokens"]
}
summary["latency_note"] = (
    "Successful responses only; failed requests have no recorded seconds. Usage excludes smoke and UI calls."
)
summary["errors"] = [
    {k: x.get(k) for k in ["case_id", "text", "expected", "predicted", "error"]}
    for x in rows
    if x["predicted"] != x["expected"]
]
(folder / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
print(json.dumps(summary, indent=2, ensure_ascii=False))
