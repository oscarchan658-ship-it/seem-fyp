"""Run the existing Rule NLU offline on approved Dataset B cases."""

import argparse
import csv
import json
from pathlib import Path
from time import perf_counter

from controller import decide_candidate
from research.dataset_b import read_cases
from rule_nlu import extract
from schemas import validate_nlu


def run(cases):
    predictions = []
    for case in cases:
        started = perf_counter()
        item_id = case["item_id"]
        candidate = validate_nlu(extract(item_id, case["text"]), item_id)
        value = decide_candidate(candidate)
        runtime_ms = (perf_counter() - started) * 1_000
        gold = case["gold_frequency"]
        if gold == "unresolved":
            outcome = "unresolved" if value is None else "accepted_unresolved"
        elif value is None:
            outcome = "abstained"
        else:
            outcome = "correct" if value == gold else "wrong"
        predictions.append(
            {
                "case_id": case["case_id"],
                "item_id": item_id,
                "gold_frequency": gold,
                "prediction": value,
                "outcome": outcome,
                "ambiguity": candidate["ambiguity"],
                "timeframe": candidate["timeframe"],
                "model_version": candidate["model_version"],
                "runtime_ms": runtime_ms,
            }
        )
    total = len(predictions)
    accepted = sum(row["prediction"] is not None for row in predictions)
    resolved = sum(row["gold_frequency"] != "unresolved" for row in predictions)
    correct = sum(row["outcome"] == "correct" for row in predictions)
    accepted_resolved = correct + sum(row["outcome"] == "wrong" for row in predictions)
    return predictions, {
        "total": total,
        "accepted": accepted,
        "abstained": total - accepted,
        "resolved_gold": resolved,
        "accepted_resolved": accepted_resolved,
        "coverage": accepted / total if total else None,
        "accepted_resolved_accuracy": correct / accepted_resolved
        if accepted_resolved
        else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    predictions, summary = run(read_cases(args.cases))
    if not predictions:
        parser.error("No cases to evaluate.")
    with args.output.open("x", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=predictions[0].keys())
        writer.writeheader()
        writer.writerows(predictions)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
