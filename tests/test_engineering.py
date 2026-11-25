import csv
import json


def test_benchmark_and_csv_figure_have_observed_source_metadata(tmp_path):
    from research.engineering import benchmark, plot_csv

    config = dict(provider="rule", mode="synthetic")
    result = benchmark(config, tmp_path / "benchmark", repetitions=5)
    assert result["calls"] == 6 and result["failures"] == 0
    assert result["warm_p95_ms"] >= result["warm_p50_ms"] >= 0
    with (tmp_path / "benchmark/timings.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        assert len(list(csv.DictReader(file))) == 6
    plot_csv(
        tmp_path / "benchmark/timings.csv",
        "call",
        "runtime_ms",
        tmp_path / "figure.png",
        mode="synthetic",
    )
    assert (tmp_path / "figure.png").stat().st_size > 1000
    metadata = json.loads((tmp_path / "figure.json").read_text())
    assert metadata["plotted_rows"] == 6 and metadata["mode"] == "synthetic"
