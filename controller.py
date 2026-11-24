from collections.abc import Callable, Mapping
from dataclasses import replace
from types import MappingProxyType
from uuid import uuid4

from phq8_engine import ConfirmedAnswer, score_phq8
from rule_nlu import extract
from safety_guard import check_safety
from schemas import Event, NluResult, SessionState, Transition, validate_nlu

_ACTIVE = (
    "START",
    "CONSENT",
    "SCREENING",
    "CLARIFICATION",
    "EDIT_ANSWER",
    "BATCH_REVIEW",
)
_ACTIONS = (
    "START",
    "ACCEPT",
    "DECLINE",
    "TEXT",
    "SELECT",
    "EDIT",
    "CANCEL_EDIT",
    "CONFIRM",
    "CANCEL",
    "RESET",
)
_ITEMS = range(1, 9)


def new_session() -> SessionState:
    return SessionState(str(uuid4()))


def decide_candidate(result: NluResult) -> int | None:
    if (
        result["timeframe"] != "past_14_days"
        or result["ambiguity"] != "none"
        or result["negation"] == "unclear"
    ):
        return None
    value = result["frequency_candidate"]
    if value == 0 and (
        result["symptom_present"] is not False or result["negation"] != "clear"
    ):
        return None
    if value and (
        result["symptom_present"] is not True or result["negation"] != "none"
    ):
        return None
    return value


def dispatch(
    state: SessionState,
    event: Event,
    *,
    guard: Callable[[str], object] = check_safety,
    nlu: Callable[[int, str], Mapping[str, object]] = extract,
) -> Transition:
    def reply(updated: SessionState, code: str) -> Transition:
        kind = event.kind if event.kind in _ACTIONS else "UNKNOWN"
        return Transition(updated, code, state.phase, kind, state.item_id)

    def advance(code: str, **changes) -> Transition:
        return reply(replace(state, revision=state.revision + 1, **changes), code)

    def clear(phase: str, code: str) -> Transition:
        safety_state = code if phase == "SAFETY_FLOW" else None
        return reply(
            SessionState(
                state.session_id, phase, state.revision + 1, safety_state=safety_state
            ),
            code,
        )

    if event.session_id != state.session_id:
        return reply(state, "rejected")
    if state.phase in _ACTIVE and event.kind == "TEXT" and isinstance(event.text, str):
        try:
            decision = guard(event.text)
        except Exception:
            decision = None
        if type(decision) is not str or decision != "normal":
            code = {"review": "safety_review", "interrupt": "safety_interrupt"}.get(
                decision if type(decision) is str else "", "safety_unavailable"
            )
            return clear("SAFETY_FLOW", code)

    if (
        type(event.expected_revision) is not int
        or event.expected_revision != state.revision
    ):
        return reply(state, "rejected")
    kind, phase = event.kind, state.phase
    if kind not in ("TEXT", "SELECT", "EDIT") and (
        event.item_id is not None or event.text is not None or event.value is not None
    ):
        return reply(state, "rejected")

    if kind == "RESET" and phase in ("RESULT", "END", "SAFETY_FLOW"):
        return reply(new_session(), "reset")
    if kind == "CANCEL" and phase != "END":
        return clear("END", "cancelled")
    if phase == "START" and kind == "START":
        return advance("consent", phase="CONSENT")
    if phase == "CONSENT" and kind == "ACCEPT":
        return advance("question", phase="SCREENING", item_id=1)
    if phase == "CONSENT" and kind == "DECLINE":
        return clear("END", "declined")

    if kind == "EDIT" and phase in ("SCREENING", "BATCH_REVIEW"):
        if (
            type(event.item_id) is int
            and event.item_id in state.provisional_answers
            and event.value is None
            and event.text is None
        ):
            return advance(
                "edit",
                phase="EDIT_ANSWER",
                item_id=event.item_id,
                return_to=(phase, state.item_id),
            )
        return reply(state, "rejected")
    if kind == "CANCEL_EDIT" and phase == "EDIT_ANSWER" and state.return_to:
        previous, item_id = state.return_to
        return advance(
            "edit_cancelled", phase=previous, item_id=item_id, return_to=None
        )

    if kind == "CONFIRM" and phase == "BATCH_REVIEW":
        if state.provisional_answers.keys() != set(_ITEMS):
            return reply(state, "scoring_unavailable")
        answers = tuple(
            ConfirmedAnswer(item_id, state.provisional_answers[item_id])
            for item_id in _ITEMS
        )
        try:
            result = score_phq8(answers)
        except Exception:
            return reply(state, "scoring_unavailable")
        return advance(
            "result", phase="RESULT", confirmed_answers=answers, result=result
        )

    if (
        phase not in ("SCREENING", "CLARIFICATION", "EDIT_ANSWER")
        or type(event.item_id) is not int
        or event.item_id != state.item_id
    ):
        return reply(state, "rejected")
    if (
        kind == "SELECT"
        and event.text is None
        and type(event.value) is int
        and 0 <= event.value <= 3
    ):
        value = event.value
    elif kind == "TEXT" and isinstance(event.text, str) and event.value is None:
        clarification_phase = (
            "EDIT_ANSWER" if phase == "EDIT_ANSWER" else "CLARIFICATION"
        )
        try:
            candidate = validate_nlu(nlu(event.item_id, event.text), event.item_id)
            value = decide_candidate(candidate)
        except Exception:
            return advance("nlu_unavailable", phase=clarification_phase)
        if value is None:
            return advance("clarify", phase=clarification_phase)
    else:
        return reply(state, "rejected")

    provisional = MappingProxyType({**state.provisional_answers, event.item_id: value})
    if phase == "EDIT_ANSWER" and state.return_to:
        previous, item_id = state.return_to
        return advance(
            "edited",
            phase=previous,
            item_id=item_id,
            return_to=None,
            provisional_answers=provisional,
        )
    next_item = next(
        (item_id for item_id in _ITEMS if item_id not in provisional), None
    )
    if next_item is None:
        return advance(
            "review",
            phase="BATCH_REVIEW",
            item_id=None,
            provisional_answers=provisional,
        )
    return advance(
        "question",
        phase="SCREENING",
        item_id=next_item,
        provisional_answers=provisional,
    )
