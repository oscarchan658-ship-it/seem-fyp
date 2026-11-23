from typing import Literal

SafetyDecision = Literal["normal", "review", "interrupt"]
MOCK_VERSION = "synthetic-guard-v1"


def check_safety(text: str) -> SafetyDecision:
    """Recognize explicit synthetic fixtures for the local-only research demo."""
    if text.strip() == "[DEMO_INTERRUPT]":
        return "interrupt"
    if text.strip() == "[DEMO_REVIEW]":
        return "review"
    return "normal"
