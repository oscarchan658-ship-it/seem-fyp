"""Offline adapters. Model artifacts, prompts and labels are supplied by the team."""

import json
import hashlib
import subprocess
from pathlib import Path

from research.providers import SentimentResult
from schemas import validate_nlu


def model_signature(config):
    keys = (
        "provider",
        "version",
        "model_path",
        "command",
        "timeout",
        "templates",
        "hypothesis_template",
        "confidence_definition",
    )
    return hashlib.sha256(
        json.dumps({key: config.get(key) for key in keys}, sort_keys=True).encode()
    ).hexdigest()


class CommandNLU:
    """Run a local structured model worker with an enforced wall-clock timeout."""

    def __init__(self, command, *, version, timeout=10):
        if (
            not isinstance(command, list)
            or not command
            or any(type(part) is not str or not part for part in command)
        ):
            raise ValueError("Expected a local argv list.")
        if not version or not 0 < timeout <= 60:
            raise ValueError("Invalid model version or timeout.")
        self.command, self.version, self.timeout = command, version, timeout

    def predict(self, request):
        data = dict(
            item_id=request.item_id,
            text=request.text,
            question_timeframe=request.question_timeframe,
            clarification=request.clarification.question
            if request.clarification
            else None,
        )
        try:
            response = subprocess.run(
                self.command,
                input=json.dumps(data, ensure_ascii=False),
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=self.timeout,
                check=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("Local model timed out.") from exc
        except subprocess.CalledProcessError as exc:
            raise ConnectionError("Local model worker failed.") from exc
        result = validate_nlu(json.loads(response.stdout), request.item_id)
        if result["model_version"] != self.version:
            raise ValueError("Unexpected model version.")
        return result


class LocalNLI:
    """NLI zero-shot templates map to team-approved complete structured states."""

    def __init__(
        self, model_path, *, version, templates, hypothesis_template, pipeline=None
    ):
        if not version or not templates or "{}" not in hypothesis_template:
            raise ValueError("Version, templates and hypothesis template are required.")
        if pipeline is None:
            from transformers import pipeline as make_pipeline
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            path = Path(model_path)
            if not path.is_dir():
                raise ValueError("Provide an existing approved local model directory.")
            model = AutoModelForSequenceClassification.from_pretrained(
                path, local_files_only=True, trust_remote_code=False
            )
            tokenizer = AutoTokenizer.from_pretrained(
                path, local_files_only=True, trust_remote_code=False
            )
            pipeline = make_pipeline(
                "zero-shot-classification", model=model, tokenizer=tokenizer, device=-1
            )
        self.pipeline, self.version, self.templates, self.hypothesis_template = (
            pipeline,
            version,
            templates,
            hypothesis_template,
        )

    def predict(self, request):
        text = f"Item {request.item_id}. Question timeframe: {request.question_timeframe}. Clarification: {request.clarification.question if request.clarification else 'none'}. Response: {request.text}"
        output = self.pipeline(
            text,
            candidate_labels=list(self.templates),
            hypothesis_template=self.hypothesis_template,
            multi_label=False,
        )
        if (
            not isinstance(output, dict)
            or not output.get("labels")
            or not output.get("scores")
        ):
            raise ValueError("Malformed NLI output.")
        label, score = output["labels"][0], output["scores"][0]
        payload = dict(
            self.templates[label],
            item_id=request.item_id,
            model_version=self.version,
            confidence_signal=score,
        )
        return validate_nlu(payload, request.item_id)


class LocalSentiment:
    def __init__(self, pipeline, *, labels, version):
        self.pipeline, self.labels, self.version = pipeline, labels, version

    def predict(self, text):
        result = self.pipeline(text)
        if not isinstance(result, list) or len(result) != 1:
            raise ValueError("Malformed sentiment output.")
        return SentimentResult(
            self.labels[result[0]["label"]], result[0]["score"], self.version
        )


def load_provider(config):
    if config["provider"] == "rule":
        from nlu_provider import RuleProvider

        return RuleProvider()
    if config["provider"] == "structured_llm":
        return CommandNLU(
            config["command"],
            version=config["version"],
            timeout=config.get("timeout", 10),
        )
    if config["provider"] == "nli":
        return LocalNLI(
            config["model_path"],
            version=config["version"],
            templates=config["templates"],
            hypothesis_template=config["hypothesis_template"],
        )
    raise ValueError("Unknown provider.")
