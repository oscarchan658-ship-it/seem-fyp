from collections.abc import Callable
from dataclasses import replace
from types import MappingProxyType
from uuid import uuid4

from evidence_manager import assess_candidate, evaluate_candidate
from nlu_provider import ClarificationContext, NLUProvider, NluRequest, RuleProvider
from phq8_engine import ConfirmedAnswer, score_phq8
from safety_guard import check_safety
from schemas import Event, LocalDayResult, NluResult, SessionState, Transition

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
    return assess_candidate(result).value


def dispatch(
    state: SessionState,
    event: Event,
    *,
    guard: Callable[[str], object] = check_safety,
    nlu: NLUProvider = RuleProvider(),
) -> Transition:
    def reply(
        updated: SessionState, code: str, reason: str | None = None
    ) -> Transition:
        kind = event.kind if event.kind in _ACTIONS else "UNKNOWN"
        return Transition(updated, code, state.phase, kind, state.item_id, reason)

    def advance(code: str, *, reason: str | None = None, **changes) -> Transition:
        changes.setdefault("clarification_item_id", None)
        return reply(
            replace(state, revision=state.revision + 1, **changes), code, reason
        )

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
    day_interval = None
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
        context = (
            ClarificationContext(event.item_id, "frequency_in_past_14_days")
            if state.clarification_item_id == event.item_id
            else None
        )
        try:
            request = NluRequest(event.item_id, event.text, clarification=context)
            payload = nlu.predict(request)
            decision = evaluate_candidate(payload, event.item_id)
            if type(payload) is LocalDayResult:
                day_interval = payload.interval
        except Exception:
            return advance(
                "nlu_unavailable",
                phase=clarification_phase,
                clarification_item_id=event.item_id,
            )
        value = decision.value
        if value is None:
            return advance(
                "clarify",
                reason=decision.reason,
                phase=clarification_phase,
                clarification_item_id=event.item_id,
            )
    else:
        return reply(state, "rejected")

    provisional = MappingProxyType({**state.provisional_answers, event.item_id: value})
    intervals = dict(state.day_intervals)
    intervals.pop(event.item_id, None)
    if day_interval is not None:
        intervals[event.item_id] = day_interval
    intervals = MappingProxyType(intervals)
    if phase == "EDIT_ANSWER" and state.return_to:
        previous, item_id = state.return_to
        return advance(
            "edited",
            phase=previous,
            item_id=item_id,
            return_to=None,
            provisional_answers=provisional,
            day_intervals=intervals,
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
            day_intervals=intervals,
        )
    return advance(
        "question",
        phase="SCREENING",
        item_id=next_item,
        provisional_answers=provisional,
        day_intervals=intervals,
    )
