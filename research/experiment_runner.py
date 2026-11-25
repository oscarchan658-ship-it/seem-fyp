"""Run frozen E2a/E2b or Validation threshold selection with offline providers."""

import argparse
import csv
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from time import perf_counter

from evidence_manager import evaluate_candidate
from nlu_provider import ClarificationContext, NluRequest
from research.annotation import _write_csv
from research.dataset_b import _validate_row, read_cases
from research.e2 import freeze_threshold, metrics
from research.local_models import load_provider, model_signature


def validate_threshold_input(cases, config, turn):
    if turn != "initial" or config.get("split_role") != "development_validation":
        raise ValueError(
            "Threshold selection requires initial-turn Development Validation."
        )
    manifest = json.loads(Path(config["dataset_manifest"]).read_text(encoding="utf-8"))
    digest = hashlib.sha256(cases.read_bytes()).hexdigest()
    if (
        digest != manifest["files"]["development_validation.jsonl"]
        or digest == manifest["files"]["locked_evaluation.jsonl"]
    ):
        raise ValueError("Validation input hash does not match the frozen manifest.")


def _pairing(cases_file, cases, metadata):
    required = (
        "followup_manifest",
        "parent_dir",
        "split_role",
        "initial_predictions",
        "initial_manifest",
    )
    if any(not metadata.get(key) for key in required):
        raise ValueError("Pilot E2b requires sealed pairing metadata.")
    frozen_path = Path(metadata["followup_manifest"])
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    split = metadata["split_role"]
    if split not in {
        "development_train",
        "development_validation",
        "locked_evaluation",
    }:
        raise ValueError("Unknown paired split.")
    digest = hashlib.sha256(cases_file.read_bytes()).hexdigest()
    if digest != frozen["files"][f"{split}.jsonl"]:
        raise ValueError("Followup data hash mismatch.")
    links_path = frozen_path.parent / "paired_cases.json"
    if (
        hashlib.sha256(links_path.read_bytes()).hexdigest()
        != frozen["files"]["paired_cases.json"]
    ):
        raise ValueError("Sealed pair mapping hash mismatch.")
    links = json.loads(links_path.read_text(encoding="utf-8"))
    expected = {key for key, value in links.items() if value["split"] == split}
    if {row["case_id"] for row in cases} != expected:
        raise ValueError("E2b must use every preselected pair in this split.")
    parent_path = Path(metadata["parent_dir"]) / f"{split}.jsonl"
    parent_hash = hashlib.sha256(parent_path.read_bytes()).hexdigest()
    if parent_hash != frozen["parent_files"][parent_path.name]:
        raise ValueError("Parent split hash mismatch.")
    parents = {row["case_id"]: row for row in read_cases(parent_path)}
    initial_manifest = json.loads(
        Path(metadata["initial_manifest"]).read_text(encoding="utf-8")
    )
    if initial_manifest["cases_sha256"] != parent_hash or initial_manifest[
        "model_signature"
    ] != model_signature(metadata):
        raise ValueError(
            "Initial predictions must use the same parent cases and model."
        )
    initial_file = Path(metadata["initial_predictions"])
    if (
        hashlib.sha256(initial_file.read_bytes()).hexdigest()
        != initial_manifest["files"]["e2a_predictions.csv"]
    ):
        raise ValueError("Initial prediction hash mismatch.")
    with initial_file.open(encoding="utf-8-sig", newline="") as file:
        predictions = {row["case_id"]: row for row in csv.DictReader(file)}
    for row in cases:
        parent = parents[links[row["case_id"]]["parent_id"]]
        if (
            row["group_id"] != parent["group_id"]
            or row["item_id"] != parent["item_id"]
            or parent["case_id"] not in predictions
        ):
            raise ValueError("Parent group/item or initial prediction mismatch.")
    return links, predictions


def run_e2(cases_file, output, *, turn, metadata, provider=None, engineering=False):
    if turn not in {"initial", "clarification"} or metadata.get("mode") not in {
        "synthetic",
        "empirical",
    }:
        raise ValueError("Specify turn and evidence mode.")
    if metadata["mode"] == "empirical" and not metadata.get("dataset_authorized"):
        raise ValueError("Dataset authorization is required.")
    cases = read_cases(cases_file)
    if not cases or len({case["case_id"] for case in cases}) != len(cases):
        raise ValueError("Expected nonempty unique cases.")
    for case in cases:
        _validate_row(case)
    if engineering and metadata["mode"] != "synthetic":
        raise ValueError("Engineering fixtures must be synthetic.")
    pairing = (
        _pairing(cases_file, cases, metadata)
        if turn == "clarification" and not engineering
        else None
    )
    try:
        provider = provider or load_provider(metadata)
    except Exception as exc:
        output.mkdir(parents=True)
        manifest = dict(
            status="NOT RUN",
            reason=type(exc).__name__,
            config=metadata,
            cases_sha256=hashlib.sha256(cases_file.read_bytes()).hexdigest(),
            turn=turn,
        )
        (output / "experiment_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        return manifest
    rows = []
    for case in cases:
        started = perf_counter()
        item = case["item_id"]
        request = NluRequest(
            item,
            case["text"],
            clarification=ClarificationContext(item, "frequency_in_past_14_days")
            if turn == "clarification"
            else None,
        )
        value, confidence, error, reason, ambiguity = None, None, None, None, None
        try:
            payload = provider.predict(request)
            decision = evaluate_candidate(payload, item)
            value, confidence, reason, ambiguity = (
                decision.value,
                payload.get("confidence_signal"),
                decision.reason,
                payload["ambiguity"],
            )
            version = payload["model_version"]
        except Exception as exc:
            error = type(exc).__name__
            version = metadata.get("version", "unavailable")
        rows.append(
            dict(
                case_id=case["case_id"],
                group_id=case["group_id"],
                item_id=item,
                gold_frequency=case["gold_frequency"],
                prediction=value,
                confidence=confidence,
                gold_ambiguity=case["ambiguity"],
                ambiguity=ambiguity,
                reason=reason,
                error=error,
                model_version=version,
                runtime_ms=(perf_counter() - started) * 1000,
            )
        )
    if len({row["model_version"] for row in rows if not row["error"]}) > 1:
        raise ValueError("Provider changed version during the experiment.")
    name = "e2a" if turn == "initial" else "e2b"
    output.mkdir(parents=True)
    _write_csv(output / f"{name}_predictions.csv", tuple(rows[0]), rows)
    _write_csv(
        output / f"{name}_errors.csv",
        tuple(rows[0]),
        (row for row in rows if row["prediction"] != row["gold_frequency"]),
    )
    summary = metrics(rows)
    # Invalid ambiguity output is a missing prediction, separately counted.
    valid_ambiguity = [row for row in rows if row["ambiguity"] is not None]
    summary["ambiguity_accuracy"] = sum(
        (row["ambiguity"] != "none") == (row["gold_ambiguity"] != "none")
        for row in valid_ambiguity
    ) / len(rows)
    summary["invalid_ambiguity_outputs"] = len(rows) - len(valid_ambiguity)
    _write_csv(
        output / f"{name}_summary.csv",
        tuple(summary),
        [
            {
                key: json.dumps(value) if isinstance(value, list) else value
                for key, value in summary.items()
            }
        ],
    )
    if pairing is not None:
        links, initial = pairing
        pairs = []
        for row in rows:
            parent_id = links[row["case_id"]]["parent_id"]
            before = initial[parent_id]
            initial_gold = before["gold_frequency"]
            initial_gold = (
                initial_gold if initial_gold == "unresolved" else int(initial_gold)
            )
            initial_prediction = (
                int(before["prediction"]) if before["prediction"] else None
            )
            pairs.append(
                dict(
                    case_id=row["case_id"],
                    parent_id=parent_id,
                    initial_gold=initial_gold,
                    initial_prediction=initial_prediction,
                    followup_gold=row["gold_frequency"],
                    followup_prediction=row["prediction"],
                    both_resolvable=initial_gold != "unresolved"
                    and row["gold_frequency"] != "unresolved",
                )
            )
        _write_csv(output / "e2b_pairs.csv", tuple(pairs[0]), pairs)
        paired_summary = dict(
            pairs=len(pairs),
            both_resolvable=sum(row["both_resolvable"] for row in pairs),
            initial_correct=sum(
                row["initial_prediction"] == row["initial_gold"] for row in pairs
            ),
            followup_correct=sum(
                row["followup_prediction"] == row["followup_gold"] for row in pairs
            ),
        )
        (output / "paired_summary.json").write_text(
            json.dumps(paired_summary, indent=2), encoding="utf-8"
        )
    manifest = dict(
        experiment_id=metadata.get("experiment_id", name + "-" + output.name),
        empirical_status="SYNTHETIC PILOT"
        if metadata["mode"] == "synthetic"
        else "EMPIRICAL",
        turn=turn,
        config=metadata,
        cases_sha256=hashlib.sha256(cases_file.read_bytes()).hexdigest(),
        git_sha=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        python=platform.python_version(),
        model_versions=sorted(
            {row["model_version"] for row in rows if not row["error"]}
        ),
        model_signature=model_signature(metadata),
        summary=summary,
    )
    manifest["files"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output.glob("*.csv")
    }
    (output / "experiment_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("cases", type=Path)
    cli.add_argument("config", type=Path)
    cli.add_argument("output", type=Path)
    cli.add_argument("--turn", choices=("initial", "clarification"), required=True)
    cli.add_argument("--validation-threshold", action="store_true")
    args = cli.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.validation_threshold:
        validate_threshold_input(args.cases, config, args.turn)
    result = run_e2(args.cases, args.output, turn=args.turn, metadata=config)
    if args.validation_threshold:
        if result.get("status") == "NOT RUN":
            raise SystemExit(
                "Model unavailable; threshold selection NOT RUN. See manifest."
            )
        import csv

        with (
            args.output
            / (
                "e2a_predictions.csv"
                if args.turn == "initial"
                else "e2b_predictions.csv"
            )
        ).open(encoding="utf-8-sig", newline="") as file:
            rows = [
                dict(
                    gold_frequency=int(row["gold_frequency"])
                    if row["gold_frequency"] != "unresolved"
                    else "unresolved",
                    prediction=int(row["prediction"]) if row["prediction"] else None,
                    confidence=float(row["confidence"]) if row["confidence"] else None,
                )
                for row in csv.DictReader(file)
            ]
        threshold = freeze_threshold(rows)
        threshold["validation_sha256"] = result["cases_sha256"]
        threshold["model_signature"] = model_signature(config)
        threshold["model_versions"] = result["model_versions"]
        threshold["selection_turn"] = "initial"
        (args.output / "threshold.json").write_text(
            json.dumps(threshold, indent=2), encoding="utf-8"
        )
    print(json.dumps(result, indent=2))
