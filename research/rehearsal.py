"""Reproduce engineering checks using separate synthetic fixtures, never Dataset B Gold."""

import argparse
import hashlib
import json
from pathlib import Path

from research.e1 import run as run_e1
from research.e3_runner import run as run_e3
from research.engineering import benchmark, plot_csv
from research.experiment_runner import run_e2
from rule_nlu import extract


def run(output, *, repetitions=2000):
    output.mkdir(parents=True)
    fixtures = output / "fixtures"
    fixtures.mkdir()
    config = dict(
        mode="synthetic", provider="rule", experiment_id="engineering-fixtures-only"
    )
    for turn in ("initial", "clarification"):
        records = [
            dict(
                case_id=f"fixture-{index}",
                group_id=f"fixture-group-{index}",
                item_id=1,
                text=("過去兩週" + label) if turn == "initial" else f"{days} days",
                gold_frequency=index,
                ambiguity="none",
                timeframe="past_14_days",
                source_id="SEPARATE_ENGINEERING_FIXTURE",
                annotation_ref="SELF_CHECK_ONLY",
            )
            for index, (label, days) in enumerate(
                zip(("完全沒有", "有幾天", "超過一半的日子", "幾乎每天"), (1, 5, 9, 14))
            )
        ]
        path = fixtures / f"{turn}.jsonl"
        path.write_text(
            "".join(
                json.dumps(record, ensure_ascii=False) + "\n" for record in records
            ),
            encoding="utf-8",
        )
        run_e2(
            path,
            output / ("e2a" if turn == "initial" else "e2b"),
            turn=turn,
            metadata=config,
            engineering=True,
        )
    features = [
        dict(
            participant_id=f"fixture-p{index}",
            case_id=f"fixture-p{index}",
            split=split,
            target=index % 2,
            sentiment_features=[float(index % 2)],
            context_features=[float(1 - index % 2)],
            divergence=False,
        )
        for split, indices in (
            ("train", range(8)),
            ("validation", range(8, 12)),
            ("test", range(12, 16)),
        )
        for index in indices
    ]
    e1config = dict(
        mode="synthetic",
        target_definition="synthetic self-check binary label",
        dataset_version="engineering-fixture-v1",
    )
    (fixtures / "e1_features.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in features), encoding="utf-8"
    )
    (fixtures / "e1_config.json").write_text(json.dumps(e1config), encoding="utf-8")
    run_e1(features, e1config, output / "e1", repetitions=repetitions)
    items = [
        dict(
            item_id=item,
            case_id=f"fixture-item-{item}",
            gold_frequency=1,
            initial=extract(item, "過去兩週有幾天"),
            replies=[
                dict(
                    turn=1, action_id="confirm-item", outcome="reply", confirmed_value=1
                )
            ],
        )
        for item in range(1, 9)
    ]
    sessions = [
        dict(
            session_id="engineering-session",
            items=items,
            batch=[
                dict(snapshot=[1] * 8, confirmed={str(item): 1 for item in range(1, 9)})
            ],
        )
    ]
    (fixtures / "e3_sessions.json").write_text(json.dumps(sessions), encoding="utf-8")
    run_e3(
        sessions,
        output / "e3",
        config=config,
        threshold_record=dict(
            status="NOT RUN", threshold=None, reason="Rule has no confidence signal."
        ),
    )
    benchmark(config, output / "benchmark")
    (output / "figures").mkdir()
    plot_csv(
        output / "e2a/e2a_predictions.csv",
        "case_id",
        "prediction",
        output / "figures/e2-initial.png",
        mode="synthetic",
    )
    plot_csv(
        output / "benchmark/timings.csv",
        "call",
        "runtime_ms",
        output / "figures/rule-latency.png",
        mode="synthetic",
    )
    plot_csv(
        output / "e1/metrics.csv",
        "arm",
        "macro_f1",
        output / "figures/e1-pipeline.png",
        mode="synthetic",
    )
    summary = dict(
        mode="ENGINEERING SELF-CHECK",
        empirical_e1="NOT RUN",
        empirical_e2="NOT RUN",
        empirical_e3="NOT RUN",
        checks=dict(e2a_cases=4, e2b_cases=4, e3_sessions=1, e1_participants=16),
        files={
            str(path.relative_to(output)).replace("\\", "/"): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
    )
    (output / "rehearsal_manifest.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))
