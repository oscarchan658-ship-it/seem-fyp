"""Deterministic, human-authored replies for an offline dialogue simulator."""

from dataclasses import dataclass
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
