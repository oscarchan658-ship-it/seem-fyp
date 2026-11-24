"""Deterministic, human-authored replies for an offline dialogue simulator."""

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType


@dataclass(frozen=True)
class OracleReply:
    text: str | None
    missing_branch: bool = False

    @property
    def outcome(self):
        if self.missing_branch:
            return "missing_branch"
        return "reply" if self.text is not None else "unresolved"


class FollowUpOracle:
    def __init__(self, replies):
        for (case_id, turn, action_id), reply in replies.items():
            if not case_id or not action_id:
                raise ValueError("Oracle case and action IDs are required.")
            if type(turn) is not int or turn < 1:
                raise ValueError("Oracle turn must be a positive integer.")
            if (
                not isinstance(reply, OracleReply)
                or reply.missing_branch
                or (
                    reply.text is not None
                    and (type(reply.text) is not str or not reply.text.strip())
                )
            ):
                raise ValueError("Invalid scripted reply.")
        self._replies = MappingProxyType(dict(replies))

    def respond(self, case_id, turn, action_id):
        if type(turn) is not int:
            return OracleReply(None, missing_branch=True)
        return self._replies.get(
            (case_id, turn, action_id), OracleReply(None, missing_branch=True)
        )


def validate_scenarios(scenarios, *, formal=False):
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("Expected a nonempty list of scenarios.")
    if formal and not 24 <= len(scenarios) <= 32:
        raise ValueError("Expected 24–32 scenarios for formal E3.")
    ids = set()
    entries = {}
    for scenario in scenarios:
        case_id = scenario["case_id"]
        if not isinstance(case_id, str) or not case_id.strip() or case_id in ids:
            raise ValueError("Invalid or duplicate scenario ID.")
        ids.add(case_id)
        for field in ("author_ref", "initial_answer", "system_clarification"):
            if not isinstance(scenario[field], str) or not scenario[field].strip():
                raise ValueError(f"Missing {field} for {case_id}.")
        item, gold = scenario["item_id"], scenario["gold_frequency"]
        if type(item) is not int or not 1 <= item <= 8:
            raise ValueError(f"Invalid item ID for {case_id}.")
        if gold != "unresolved" and (type(gold) is not int or not 0 <= gold <= 3):
            raise ValueError(f"Invalid gold outcome for {case_id}.")
        outcomes = set()
        for branch in scenario["branches"]:
            key = (case_id, branch["turn"], branch["action_id"])
            outcome, reply = branch["outcome"], branch["text"]
            if (
                type(key[1]) is not int
                or not isinstance(key[2], str)
                or not key[2].strip()
                or key in entries
                or outcome not in {"reply", "unresolved", "refusal"}
                or (outcome == "reply") != (reply is not None)
            ):
                raise ValueError(f"Invalid or duplicate Oracle branch for {case_id}.")
            outcomes.add(outcome)
            entries[key] = OracleReply(reply)
        if "reply" not in outcomes or not outcomes & {"unresolved", "refusal"}:
            raise ValueError(
                f"Missing reply or unresolved/refusal branch for {case_id}."
            )
    FollowUpOracle(entries)
    return {"scenarios": len(ids), "branches": len(entries)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("scenarios", type=Path)
    cli.add_argument("--formal", action="store_true")
    args = cli.parse_args()
    data = args.scenarios.read_bytes()
    result = validate_scenarios(json.loads(data), formal=args.formal)
    print(json.dumps({**result, "sha256": hashlib.sha256(data).hexdigest()}, indent=2))
