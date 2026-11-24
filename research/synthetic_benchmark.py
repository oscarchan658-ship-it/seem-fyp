"""Measure the local Rule provider on one explicit synthetic fixture."""

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
import tracemalloc
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter_ns

from nlu_provider import NluRequest, RuleProvider


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--warm-runs", type=int, default=30)
    args = parser.parse_args()
    if args.warm_runs < 1:
        parser.error("At least one warm run is required.")
    request = NluRequest(1, "過去兩週有幾天")
    provider = RuleProvider()
    rows = []
    model_version = None
    for index in range(args.warm_runs + 1):
        tracemalloc.start()
        start = perf_counter_ns()
        try:
            response = provider.predict(request)
            model_version = response["model_version"]
            state = "pass" if response["frequency_candidate"] == 1 else "unexpected"
        except Exception:
            state = "error"
        finally:
            elapsed = (perf_counter_ns() - start) / 1_000_000
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        rows.append(
            {
                "run": index,
                "phase": "first_call" if index == 0 else "warm",
                "latency_ms": elapsed,
                "python_peak_bytes": peak,
                "state": state,
                "tokens": None,
                "cost": None,
            }
        )
    warm = sorted(row["latency_ms"] for row in rows[1:] if row["state"] == "pass")
    digest = hashlib.sha256(request.text.encode()).hexdigest()
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
    )
    metadata = {
        "experiment_id": f"rule-synthetic-{sha[:8]}-{digest[:8]}",
        "git_sha": sha,
        "worktree_dirty": dirty,
        "executed_at_utc": datetime.now(UTC).isoformat(),
        "timing_method": "perf_counter_ns with tracemalloc active",
        "fixture_sha256": digest,
        "model": model_version,
        "environment": platform.platform(),
        "python": platform.python_version(),
        "streamlit": version("streamlit"),
        "fixture": "one synthetic response",
        "warm_successes": len(warm),
        "failures": sum(row["state"] != "pass" for row in rows),
        "warm_p95_ms": warm[math.ceil(0.95 * len(warm)) - 1] if warm else None,
    }
    args.output.mkdir()
    with (args.output / "timings.csv").open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "manifest.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))
    return int(metadata["failures"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
