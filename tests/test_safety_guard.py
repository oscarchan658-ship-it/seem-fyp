import pytest

from safety_guard import check_safety


@pytest.mark.parametrize(
    ("text", "decision"),
    [
        ("[DEMO_INTERRUPT]", "interrupt"),
        (" [DEMO_REVIEW] ", "review"),
        ("虛構例句：笑死我了。", "normal"),
        ("我在引用 [DEMO_INTERRUPT] 這個標記", "normal"),
    ],
)
def test_synthetic_guard_fixtures_only(text, decision):
    assert check_safety(text) == decision
