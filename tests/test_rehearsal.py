def test_rehearsal_produces_traceable_synthetic_artifacts(tmp_path):
    from research.rehearsal import run

    result = run(tmp_path / "rehearsal", repetitions=20)
    assert (
        result["empirical_e1"]
        == result["empirical_e2"]
        == result["empirical_e3"]
        == "NOT RUN"
    )
    assert (tmp_path / "rehearsal/e1/bootstrap_ci.csv").exists()
    assert (tmp_path / "rehearsal/figures/e2-initial.png").exists()
    assert result["checks"]["e2a_cases"] == result["checks"]["e2b_cases"] == 4
