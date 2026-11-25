"""Freeze actual local model outputs for every human-authored E3 reply branch."""

import argparse
import hashlib
import json
from pathlib import Path

from nlu_provider import ClarificationContext, NluRequest
from research.local_models import load_provider, model_signature
from schemas import validate_nlu


def freeze(sessions, output, *, config, provider=None):
    if not sessions or config.get("mode") not in {"synthetic", "empirical"}:
        raise ValueError("Specify nonempty authored sessions and mode.")
    if config["mode"] == "empirical" and (
        not config.get("human_oracle_reviewed") or not 24 <= len(sessions) <= 32
    ):
        raise ValueError(
            "Formal Oracle requires 24–32 reviewed human-authored sessions."
        )
    provider = provider or load_provider(config)
    frozen = []
    for session in sessions:
        if (
            not session.get("author_ref", "").strip()
            or {row["item_id"] for row in session["items"]} != set(range(1, 9))
            or len(session["items"]) != 8
        ):
            raise ValueError("Human author and eight unique items are required.")
        items = []
        for row in session["items"]:
            item = row["item_id"]

            def predict(text, clarification):
                if not isinstance(text, str) or not text.strip():
                    raise ValueError("Missing authored reply.")
                request = NluRequest(
                    item,
                    text,
                    clarification=ClarificationContext(
                        item, "frequency_in_past_14_days"
                    )
                    if clarification
                    else None,
                )
                raw = provider.predict(request)
                validate_nlu(raw, item)
                return dict(raw)

            initial = predict(row["initial_answer"], False)
            replies = []
            for reply in row["replies"]:
                branch = {key: reply[key] for key in ("turn", "action_id", "outcome")}
                if (
                    reply["outcome"] == "reply"
                    and reply["action_id"] == "clarify-frequency"
                ):
                    branch["prediction"] = predict(reply["text"], True)
                    if config["provider"] == "rule":
                        branch["request"] = dict(text=reply["text"], clarification=True)
                elif reply["outcome"] == "reply" and reply["action_id"] in {
                    "confirm-item",
                    "confirm-batch",
                }:
                    value = reply["confirmed_value"]
                    if type(value) is not int or not 0 <= value <= 3:
                        raise ValueError(
                            "Confirmation requires an explicit human-authored 0–3 reply."
                        )
                    branch["confirmed_value"] = value
                elif reply["outcome"] != "unresolved":
                    raise ValueError("Unsupported Oracle action or outcome.")
                replies.append(branch)
            entry = dict(
                item_id=item,
                case_id=row["case_id"],
                gold_frequency=row["gold_frequency"],
                initial=initial,
                replies=replies,
            )
            if config["provider"] == "rule":
                entry["initial_request"] = dict(
                    text=row["initial_answer"], clarification=False
                )
            items.append(entry)
        frozen.append(
            dict(
                session_id=session["session_id"],
                author_ref=session["author_ref"],
                items=items,
                batch=session["batch"],
            )
        )
    # Validate all scripts before producing a frozen input file.
    from research.e3_runner import _items

    for session in frozen:
        _items(session, config["provider"])
    with output.open("x", encoding="utf-8") as file:
        json.dump(frozen, file, ensure_ascii=False, indent=2)
    output.with_suffix(".manifest.json").write_text(
        json.dumps(
            dict(
                model_signature=model_signature(config),
                config=config,
                authored_source_sha256=hashlib.sha256(
                    json.dumps(sessions, sort_keys=True).encode()
                ).hexdigest(),
                frozen_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    return frozen


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sessions", "config", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    freeze(
        json.loads(args.sessions.read_text(encoding="utf-8")),
        args.output,
        config=json.loads(args.config.read_text(encoding="utf-8")),
    )
