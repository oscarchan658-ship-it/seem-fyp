"""Replay frozen eight-item questionnaires under P0–P3 with one shared Oracle."""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from research.annotation import _write_csv
from research.policy_simulator import (
    FrozenPrediction,
    ScriptedReply,
    replay_questionnaire,
)
from schemas import validate_nlu
from nlu_provider import ClarificationContext, NluRequest, RuleProvider
from research.local_models import model_signature
from research.evaluation import risk_coverage, observed_aurc
from evidence_manager import evaluate_candidate


def load_frozen_sessions(path, config):
    record = json.loads(path.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    if record["frozen_sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
        raise ValueError("Frozen prediction file hash mismatch.")
    if record["model_signature"] != model_signature(config):
        raise ValueError("Frozen prediction model signature mismatch.")
    return json.loads(path.read_text(encoding="utf-8"))


def _prediction(payload, item, provider, request=None):
    candidate = validate_nlu(payload, item)
    if request is not None:
        if provider != "rule" or type(request.get("clarification")) is not bool:
            raise ValueError(
                "Local day reconstruction requires an explicit Rule request."
            )
        local = RuleProvider().predict(
            NluRequest(
                item,
                request["text"],
                clarification=ClarificationContext(item, "frequency_in_past_14_days")
                if request["clarification"]
                else None,
            )
        )
        if dict(local) != candidate:
            raise ValueError(
                "Frozen Rule prediction does not match the recorded request."
            )
        candidate = local
    return FrozenPrediction(provider, candidate)


def _items(session, provider):
    items = {}
    for row in session["items"]:
        item = row["item_id"]
        if type(item) is not int or item in items or not 1 <= item <= 8:
            raise ValueError("Expected unique item IDs 1–8.")
        gold = row["gold_frequency"]
        gold = None if gold == "unresolved" else gold
        replies = {}
        for reply in row["replies"]:
            key = (reply["turn"], reply["action_id"])
            if key in replies:
                raise ValueError("Duplicate Oracle branch.")
            prediction = (
                _prediction(reply["prediction"], item, provider, reply.get("request"))
                if "prediction" in reply
                else None
            )
            replies[key] = ScriptedReply(
                reply["outcome"], prediction, reply.get("confirmed_value")
            )
        items[item] = (
            row["case_id"],
            _prediction(row["initial"], item, provider, row.get("initial_request")),
            gold,
            replies,
        )
    return items


def run(sessions, output, *, config, threshold_record):
    if not sessions or config.get("mode") not in {"synthetic", "empirical"}:
        raise ValueError("Nonempty sessions and evidence mode are required.")
    if config["mode"] == "empirical" and not config.get("human_oracle_reviewed"):
        raise ValueError(
            "Freeze the human-reviewed Oracle before empirical policy replay."
        )
    if len({session["session_id"] for session in sessions}) != len(sessions):
        raise ValueError("Duplicate session IDs.")
    threshold = (
        threshold_record.get("threshold")
        if threshold_record.get("status") == "FROZEN"
        else None
    )
    if threshold is not None and (
        threshold_record.get("model_signature") != model_signature(config)
        or threshold_record.get("selection_turn") != "initial"
        or not threshold_record.get("validation_sha256")
    ):
        raise ValueError(
            "Threshold must be bound to this model and frozen initial-turn Validation."
        )
    frozen_items = [_items(session, config["provider"]) for session in sessions]
    versions = {
        initial.payload["model_version"]
        for items in frozen_items
        for _, initial, _, _ in items.values()
    }
    if (
        len(versions) != 1
        or threshold is not None
        and versions != set(threshold_record.get("model_versions", []))
    ):
        raise ValueError("Frozen policy input model versions do not match.")
    curve_rows = []
    aurc = None
    if threshold is not None:
        records = []
        for items in frozen_items:
            for _, initial, gold, _ in items.values():
                payload = initial.payload
                if initial.local_interval is not None:
                    from schemas import LocalDayResult

                    payload = LocalDayResult(payload, initial.local_interval)
                decision = evaluate_candidate(payload, payload["item_id"])
                records.append(
                    (
                        payload.get("confidence_signal"),
                        gold is not None and decision.value == gold,
                        decision.value is not None,
                    )
                )
        points = risk_coverage(records, threshold_record["grid"])
        curve_rows = [
            dict(threshold=point.threshold, coverage=point.coverage, risk=point.risk)
            for point in points
        ]
        aurc = observed_aurc(points)
    rows, traces, summaries = [], [], {}
    for policy in ("P0", "P1", "P2", "P3"):
        if policy in {"P2", "P3"} and threshold is None:
            summaries[policy] = dict(
                status="NOT RUN", reason="No frozen Validation threshold."
            )
            continue
        policy_rows = []
        for session in sessions:
            items = _items(session, config["provider"])
            batch = {}
            for branch in session["batch"]:
                snapshot = tuple(branch["snapshot"])
                if (
                    snapshot in batch
                    or len(snapshot) != 8
                    or any(
                        type(value) is not int or not 0 <= value <= 3
                        for value in snapshot
                    )
                ):
                    raise ValueError("Invalid or duplicate batch snapshot.")
                batch[snapshot] = {
                    int(item): value for item, value in branch["confirmed"].items()
                }
            replays, confirmed, result, confirmations, error, batch_status = (
                replay_questionnaire(
                    items,
                    policy,
                    batch_oracle=batch if policy in {"P1", "P2"} else None,
                    threshold=threshold,
                    max_clarifications=2,
                )
            )
            for item, replay in replays.items():
                traces.append(
                    dict(
                        session_id=session["session_id"], item_id=item, **asdict(replay)
                    )
                )
            row = dict(
                session_id=session["session_id"],
                policy=policy,
                clarifications=sum(
                    replay.clarifications for replay in replays.values()
                ),
                confirmation_actions=confirmations,
                completed=result is not None,
                final_score=result.total if result else None,
                final_score_error=error,
                unresolved_items=sum(
                    replay.outcome
                    in {"unresolved", "budget_exhausted", "no_prediction"}
                    for replay in replays.values()
                ),
                missing_branches=sum(
                    replay.outcome == "missing_branch" for replay in replays.values()
                )
                + int(batch_status == "missing_branch"),
                batch_status=batch_status,
            )
            rows.append(row)
            policy_rows.append(row)
        errors = [
            row["final_score_error"]
            for row in policy_rows
            if row["final_score_error"] is not None
        ]
        summaries[policy] = dict(
            status="RUN",
            sessions=len(sessions),
            completion_rate=sum(row["completed"] for row in policy_rows) / len(sessions)
            if policy != "P0"
            else None,
            confirmation_actions=sum(
                row["confirmation_actions"] for row in policy_rows
            ),
            mean_clarifications=sum(row["clarifications"] for row in policy_rows)
            / len(sessions),
            score_error_count=len(errors),
            mean_final_score_error=sum(errors) / len(errors) if errors else None,
            missing_branches=sum(row["missing_branches"] for row in policy_rows),
        )
    output.mkdir(parents=True)
    _write_csv(output / "e3_policy_results.csv", tuple(rows[0]), rows)
    _write_csv(
        output / "risk_coverage.csv", ("threshold", "coverage", "risk"), curve_rows
    )
    (output / "e3_case_traces.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in traces),
        encoding="utf-8",
    )
    manifest = dict(
        config=config,
        threshold=threshold_record,
        max_clarifications=2,
        policies=summaries,
        input_sha256=hashlib.sha256(
            json.dumps(sessions, sort_keys=True).encode()
        ).hexdigest(),
        empirical_status="SYNTHETIC PILOT"
        if config["mode"] == "synthetic"
        else "EMPIRICAL",
        observed_aurc=aurc,
        risk_coverage_status="RUN" if curve_rows else "NOT RUN",
    )
    (output / "experiment_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for field in ("sessions", "config", "threshold", "output"):
        cli.add_argument(field, type=Path)
    args = cli.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    print(
        json.dumps(
            run(
                load_frozen_sessions(args.sessions, config),
                args.output,
                config=config,
                threshold_record=json.loads(args.threshold.read_text(encoding="utf-8")),
            ),
            indent=2,
        )
    )
