from __future__ import annotations

from application.use_cases import health_check


class FakeChecker:
    def __init__(self, result: dict) -> None:
        self._result = result

    def check(self) -> dict:
        return dict(self._result)


def test_health_check_missing_env() -> None:
    checker = FakeChecker(
        {"chatwoot": {"ok": False}, "mysql": {"ok": False}}
    )
    results = health_check.run_health_checks(checker)
    assert results["ok"] is False


def test_health_check_success() -> None:
    checker = FakeChecker(
        {"chatwoot": {"ok": True}, "mysql": {"ok": True}}
    )
    results = health_check.run_health_checks(checker)
    assert results["ok"] is True
