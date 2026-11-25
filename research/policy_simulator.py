"""Replay a single questionnaire item using frozen predictions and scripted replies."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

from evidence_manager import assess_candidate
from phq8_engine import ConfirmedAnswer, score_phq8
from schemas import LocalDayResult, validate_nlu

P0_LABEL = "No-clarification model baseline"


@dataclass(frozen=True)
class FrozenPrediction:
    provider: str
    payload: Mapping[str, object]
    local_interval: tuple | None = field(default=None, init=False)

    def __post_init__(self):
        if not self.provider:
            raise ValueError("Missing provider identifier.")
        if type(self.payload) is LocalDayResult:
            object.__setattr__(self, "local_interval", self.payload.interval)
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True)
class ScriptedReply:
    outcome: Literal["reply", "unresolved"]
    prediction: FrozenPrediction | None = None
    confirmed_value: int | None = None


@dataclass(frozen=True)
class Action:
    turn: int
    action_id: str
    reason: str
    candidate: int | None


@dataclass(frozen=True)
class Replay:
    case_id: str
    policy: str
    outcome: str
    reason: str
    candidate: int | None
    confirmed: int | None
    error: int | None
    trace: tuple[Action, ...]

    @property
    def policy_label(self):
        return P0_LABEL if self.policy == "P0" else self.policy

    @property
    def clarifications(self):
        return sum(step.action_id == "clarify-frequency" for step in self.trace)


def simulate(
    case_id,
    item_id,
    initial,
    gold,
    policy,
    oracle,
    *,
    threshold=None,
    max_clarifications=2,
    defer_batch=False,
):
    if policy not in {"P0", "P1", "P2", "P3"}:
        raise ValueError("Unknown policy.")
    if type(max_clarifications) is not int or max_clarifications < 0:
        raise ValueError("Invalid clarification budget.")
    if policy in {"P2", "P3"} and (
        type(threshold) not in {int, float} or not 0 <= threshold <= 1
    ):
        raise ValueError("Threshold must be in [0, 1].")
    if gold is not None and (type(gold) is not int or not 0 <= gold <= 3):
        raise ValueError("Invalid gold value.")

    trace = []
    current = initial
    version = initial.payload.get("model_version")
    value = None
    reason = "frequency_missing"

    def finish(outcome, confirmed=None):
        observed = value if policy == "P0" else confirmed
        error = (
            abs(observed - gold) if observed is not None and gold is not None else None
        )
        return Replay(
            case_id, policy, outcome, reason, value, confirmed, error, tuple(trace)
        )

    for turn in range(1, max_clarifications + 2):
        if (
            current.provider != initial.provider
            or current.payload.get("model_version") != version
        ):
            raise ValueError("A policy replay must use one provider and model version.")
        try:
            payload = (
                LocalDayResult(current.payload, current.local_interval)
                if current.local_interval is not None
                else current.payload
            )
            candidate = validate_nlu(payload, item_id)
        except ValueError:
            value, reason = None, "invalid_evidence"
        else:
            if policy == "P0":
                value = candidate["frequency_candidate"]
                reason = "offline_only" if value is not None else "frequency_missing"
                return finish(
                    "offline_prediction" if value is not None else "no_prediction"
                )
            decision = assess_candidate(candidate)
            value, reason = decision.value, decision.reason
            confidence = candidate.get("confidence_signal")
            if value is not None and policy in {"P2", "P3"}:
                if confidence is None:
                    value, reason = None, "missing_confidence"
                elif confidence < threshold:
                    value, reason = None, "below_threshold"
        if policy == "P0":
            return finish("no_prediction")
        if value is not None:
            if defer_batch and policy in {"P1", "P2"}:
                return finish("ready_for_batch")
            action = "confirm-item" if policy == "P3" else "confirm-batch"
        elif turn > max_clarifications:
            return finish("budget_exhausted")
        else:
            action = "clarify-frequency"

        trace.append(Action(turn, action, reason, value))
        reply = oracle.get((turn, action))
        if reply is None:
            return finish("missing_branch")
        if reply.outcome == "unresolved":
            return finish("unresolved")
        if reply.outcome != "reply":
            raise ValueError("Invalid oracle outcome.")
        if action == "clarify-frequency":
            if reply.prediction is None or reply.confirmed_value is not None:
                raise ValueError("A clarification reply needs a frozen prediction.")
            current = reply.prediction
        else:
            confirmed = reply.confirmed_value
            if (
                type(confirmed) is not int
                or not 0 <= confirmed <= 3
                or reply.prediction
            ):
                raise ValueError("A confirmation reply needs an explicit 0–3 value.")
            return finish("confirmed", confirmed)
    raise AssertionError("Clarification budget did not terminate replay.")


def replay_questionnaire(
    items, policy, *, batch_oracle=None, threshold=None, max_clarifications=2
):
    """Items map each item ID to (case ID, initial prediction, gold, oracle)."""
    if set(items) != set(range(1, 9)) or any(type(item) is not int for item in items):
        raise ValueError("Expected eight unique questionnaire items.")
    batch = policy in {"P1", "P2"}
    if batch_oracle is not None and not batch:
        raise ValueError("A batch reply is only valid for a batch policy.")
    if (
        len(
            {
                (initial.provider, initial.payload.get("model_version"))
                for _, initial, _, _ in items.values()
            }
        )
        != 1
    ):
        raise ValueError("A questionnaire must use one provider and model version.")
    replays = {
        item: simulate(
            case_id,
            item,
            initial,
            gold,
            policy,
            oracle,
            threshold=threshold,
            max_clarifications=max_clarifications,
            defer_batch=batch,
        )
        for item, (case_id, initial, gold, oracle) in sorted(items.items())
    }
    confirmed = {
        item: row.confirmed
        for item, row in replays.items()
        if row.confirmed is not None
    }
    confirmations = sum(
        step.action_id == "confirm-item"
        for row in replays.values()
        for step in row.trace
    )
    batch_status = "not_attempted"
    if batch and all(row.outcome == "ready_for_batch" for row in replays.values()):
        confirmations = 1
        snapshot = tuple(row.candidate for row in replays.values())
        if batch_oracle is None or snapshot not in batch_oracle:
            batch_status = "missing_branch"
        else:
            reply = batch_oracle[snapshot]
            if not isinstance(reply, Mapping):
                raise ValueError(
                    "Batch confirmation must be a mapping of unique item IDs."
                )
            confirmed = dict(reply)
            batch_status = (
                "confirmed" if confirmed.keys() == items.keys() else "unresolved"
            )
    result = None
    if confirmed.keys() == items.keys():
        result = score_phq8(
            tuple(ConfirmedAnswer(item, value) for item, value in confirmed.items())
        )
    elif set(confirmed) - items.keys() or any(
        type(item) is not int or type(value) is not int or not 0 <= value <= 3
        for item, value in confirmed.items()
    ):
        raise ValueError("Invalid confirmed answers.")
    gold = [item[2] for item in items.values()]
    error = (
        abs(result.total - sum(gold))
        if result is not None and None not in gold
        else None
    )
    return replays, confirmed, result, confirmations, error, batch_status


def compare_questionnaire(items, batch_oracle, *, threshold, max_clarifications=2):
    """Evaluate P0–P3 with the same frozen input, scripts and clarification budget."""
    frozen = {
        item: (case_id, initial, gold, dict(oracle))
        for item, (case_id, initial, gold, oracle) in items.items()
    }
    batch = {
        key: dict(reply) if isinstance(reply, Mapping) else reply
        for key, reply in batch_oracle.items()
    }
    return {
        policy: replay_questionnaire(
            frozen,
            policy,
            batch_oracle=batch if policy in {"P1", "P2"} else None,
            threshold=threshold,
            max_clarifications=max_clarifications,
        )
        for policy in ("P0", "P1", "P2", "P3")
    }
