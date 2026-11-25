"""Observed offline benchmark and CSV-backed scientific figures."""

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
import tracemalloc
from pathlib import Path
from time import perf_counter

from nlu_provider import NluRequest
from research.annotation import _write_csv
from research.local_models import load_provider
from schemas import validate_nlu


def benchmark(config, output, *, repetitions=30):
    if type(repetitions) is not int or repetitions < 2:
        raise ValueError("Need at least two warm observations.")
    if config.get("mode") not in {"synthetic", "empirical"}:
        raise ValueError("Specify evidence mode.")
    started = perf_counter()
    provider = load_provider(config)
    load_ms = (perf_counter() - started) * 1000
    tracemalloc.start()
    rows = []
    for call in range(repetitions + 1):
        start = perf_counter()
        error = None
        try:
            validate_nlu(provider.predict(NluRequest(1, "過去兩週有幾天")), 1)
        except Exception as exc:
            error = type(exc).__name__
        rows.append(
            dict(
                call=call,
                phase="cold" if call == 0 else "warm",
                runtime_ms=(perf_counter() - start) * 1000,
                error=error,
            )
        )
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    warm = sorted(row["runtime_ms"] for row in rows[1:])
    output.mkdir(parents=True)
    _write_csv(output / "timings.csv", tuple(rows[0]), rows)
    result = dict(
        config=config,
        mode=config["mode"],
        calls=len(rows),
        workload="single synthetic item-1 initial response",
        model_load_ms=load_ms,
        cold_inference_ms=rows[0]["runtime_ms"],
        warm_p50_ms=statistics.median(warm),
        warm_p95_ms=warm[math.ceil(0.95 * len(warm)) - 1],
        failures=sum(row["error"] is not None for row in rows),
        failure_rate=sum(row["error"] is not None for row in rows) / len(rows),
        python_tracemalloc_peak_bytes=peak,
        process_rss_bytes=None,
        tokens=None,
        cost=None,
        python=platform.python_version(),
        instrumentation="tracemalloc active during inference; excludes native model allocations",
        timings_sha256=hashlib.sha256(
            (output / "timings.csv").read_bytes()
        ).hexdigest(),
    )
    (output / "manifest.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


def plot_csv(source, x, y, output, *, mode):
    if mode not in {"synthetic", "empirical"}:
        raise ValueError("Declare figure evidence mode.")
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    with source.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    values = [
        (row[x], float(row[y])) for row in rows if row[y] not in ("", "null", "None")
    ]
    if not values or any(not math.isfinite(value) for _, value in values):
        raise ValueError("Figure needs finite observed values.")
    figure, axis = plt.subplots(figsize=(7, 4), layout="constrained")
    axis.bar(
        [label for label, _ in values], [value for _, value in values], color="#315b83"
    )
    if len(values) > 12:
        positions = list(range(0, len(values), math.ceil(len(values) / 12)))
        axis.set_xticks(positions, [values[index][0] for index in positions])
    axis.set(
        xlabel=x,
        ylabel=y,
        title=f"{'Synthetic engineering check' if mode == 'synthetic' else 'Empirical evaluation'} — {y}",
    )
    figure.savefig(output, dpi=180)
    plt.close(figure)
    output.with_suffix(".json").write_text(
        json.dumps(
            dict(
                source_file=str(source),
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                x=x,
                y=y,
                mode=mode,
                plotted_rows=len(values),
            ),
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    bench = commands.add_parser("benchmark")
    bench.add_argument("config", type=Path)
    bench.add_argument("output", type=Path)
    bench.add_argument("--repetitions", type=int, default=30)
    plot = commands.add_parser("plot")
    plot.add_argument("source", type=Path)
    plot.add_argument("x")
    plot.add_argument("y")
    plot.add_argument("output", type=Path)
    plot.add_argument("--mode", choices=("synthetic", "empirical"), required=True)
    args = cli.parse_args()
    if args.command == "benchmark":
        print(
            json.dumps(
                benchmark(
                    json.loads(args.config.read_text(encoding="utf-8")),
                    args.output,
                    repetitions=args.repetitions,
                ),
                indent=2,
            )
        )
    else:
        plot_csv(args.source, args.x, args.y, args.output, mode=args.mode)
