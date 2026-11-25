import json
import sys

import pytest

from nlu_provider import NluRequest


def test_local_command_adapter_rejects_wrong_item_and_timeout():
    from research.local_models import CommandNLU

    payload = {
        "item_id": 2,
        "frequency_candidate": 1,
        "timeframe": "past_14_days",
        "symptom_present": True,
        "negation": "none",
        "ambiguity": "none",
        "model_version": "fixture",
    }
    command = [sys.executable, "-c", f"print({json.dumps(json.dumps(payload))})"]
    with pytest.raises(ValueError):
        CommandNLU(command, version="fixture").predict(NluRequest(1, "synthetic"))
    with pytest.raises(TimeoutError):
        CommandNLU(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            version="fixture",
            timeout=0.01,
        ).predict(NluRequest(1, "synthetic"))


def test_nli_schema_validation_rejects_malformed_and_nonfinite_output():
    from research.local_models import LocalNLI
    from rule_nlu import extract

    template = extract(1, "過去兩週有幾天")
    for key in ("item_id", "model_version"):
        template.pop(key)
    malformed = LocalNLI(
        None,
        version="fixture",
        templates={"label": template},
        hypothesis_template="{}",
        pipeline=lambda *args, **kwargs: {},
    )
    with pytest.raises(ValueError, match="Malformed"):
        malformed.predict(NluRequest(1, "fixture"))
    nonfinite = LocalNLI(
        None,
        version="fixture",
        templates={"label": template},
        hypothesis_template="{}",
        pipeline=lambda *args, **kwargs: dict(labels=["label"], scores=[float("nan")]),
    )
    with pytest.raises(ValueError, match="confidence"):
        nonfinite.predict(NluRequest(1, "fixture"))


def test_e2_runner_emits_aligned_initial_and_clarification_outputs(tmp_path):
    from research.experiment_runner import run_e2

    cases = [
        dict(
            case_id="c1",
            group_id="g1",
            item_id=1,
            text="1 day",
            gold_frequency=0,
            ambiguity="none",
            timeframe="past_14_days",
            source_id="synthetic",
            annotation_ref="fixture",
        )
    ]
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(cases[0]) + "\n")
    metadata = dict(mode="synthetic", provider="rule")
    initial = run_e2(path, tmp_path / "initial", turn="initial", metadata=metadata)
    followup = run_e2(
        path,
        tmp_path / "followup",
        turn="clarification",
        metadata=metadata,
        engineering=True,
    )
    assert initial["summary"]["accepted"] == 0
    assert followup["summary"]["frequency_accuracy"] == 1
    assert followup["empirical_status"] == "SYNTHETIC PILOT"
    assert (tmp_path / "followup/e2b_predictions.csv").exists()


def test_e1_same_family_budget_and_paired_comparison(tmp_path):
    from research.e1 import run

    rows = [
        dict(
            participant_id=f"p{index}",
            case_id=f"p{index}",
            split=split,
            target=label,
            sentiment_features=[float(label)],
            context_features=[float(1 - label)],
            divergence=False,
        )
        for split, indices in (
            ("train", range(8)),
            ("validation", range(8, 12)),
            ("test", range(12, 16)),
        )
        for index in indices
        for label in [index % 2]
    ]
    config = dict(
        mode="synthetic",
        target_definition="fictional binary test label",
        dataset_version="test",
    )
    result = run(rows, config, tmp_path / "e1", repetitions=20)
    assert set(result["models"]) == {"S", "N", "F"}
    assert all(model["tuning_trials"] == 5 for model in result["models"].values())
    assert result["primary_comparison"] == "F-N"
    assert result["empirical_e1"] == "NOT RUN"
    assert (tmp_path / "e1/bootstrap_ci.csv").exists()
    rows[-1]["participant_id"] = rows[0]["participant_id"]
    with pytest.raises(ValueError, match="participant"):
        run(rows, config, tmp_path / "bad", repetitions=20)


def test_model_load_failure_leaves_not_run_manifest(tmp_path):
    from research.experiment_runner import run_e2

    cases = tmp_path / "cases.jsonl"
    cases.write_text(
        json.dumps(
            dict(
                case_id="c",
                group_id="g",
                item_id=1,
                text="fixture",
                gold_frequency=1,
                ambiguity="none",
                timeframe="past_14_days",
                source_id="fixture",
                annotation_ref="fixture",
            )
        )
        + "\n"
    )
    result = run_e2(
        cases,
        tmp_path / "failed",
        turn="initial",
        metadata=dict(provider="missing-model", mode="synthetic"),
    )
    assert result["status"] == "NOT RUN" and result["reason"] == "ValueError"
    assert (tmp_path / "failed/experiment_manifest.json").exists()


def test_e2b_pilot_requires_sealed_pairing_metadata(tmp_path):
    from research.experiment_runner import run_e2

    cases = tmp_path / "cases.jsonl"
    cases.write_text(
        json.dumps(
            dict(
                case_id="F-c",
                group_id="g",
                item_id=1,
                text="1 day",
                gold_frequency=0,
                ambiguity="none",
                timeframe="past_14_days",
                source_id="fixture",
                annotation_ref="fixture",
            )
        )
        + "\n"
    )
    with pytest.raises(ValueError, match="pair"):
        run_e2(
            cases,
            tmp_path / "bad",
            turn="clarification",
            metadata=dict(
                mode="synthetic",
                provider="rule",
                dataset_version="dataset-b-synthetic-pilot-v1",
            ),
        )
