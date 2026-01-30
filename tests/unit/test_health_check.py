from __future__ import annotations

from typing import Any

from application.use_cases import health_check


class FakeChatwootClient:
    def __init__(self, config: Any, logger: Any = None) -> None:
        self.config = config
        self.logger = logger

    def check_connection(self) -> dict[str, Any]:
        return {"ok": True}


def test_health_check_missing_env(monkeypatch) -> None:
    monkeypatch.delenv("CHATWOOT_BASE_URL", raising=False)
    monkeypatch.delenv("CHATWOOT_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("CHATWOOT_API_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("MYSQL_HOST", raising=False)
    monkeypatch.delenv("MYSQL_USER", raising=False)
    monkeypatch.delenv("MYSQL_PASSWORD", raising=False)
    monkeypatch.delenv("MYSQL_DB", raising=False)
    monkeypatch.delenv("MYSQL_PORT", raising=False)

    results = health_check.run_health_checks()
    assert results["ok"] is False
    assert results["chatwoot"]["ok"] is False
    assert results["mysql"]["ok"] is False


def test_health_check_success(monkeypatch) -> None:
    monkeypatch.setenv("CHATWOOT_BASE_URL", "https://chatwoot.local")
    monkeypatch.setenv("CHATWOOT_ACCOUNT_ID", "1")
    monkeypatch.setenv("CHATWOOT_API_ACCESS_TOKEN", "token")
    monkeypatch.setenv("MYSQL_HOST", "localhost")
    monkeypatch.setenv("MYSQL_USER", "root")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")
    monkeypatch.setenv("MYSQL_DB", "db")
    monkeypatch.setenv("MYSQL_PORT", "3306")

    monkeypatch.setattr(health_check, "ChatwootClient", FakeChatwootClient)
    monkeypatch.setattr(health_check, "check_mysql", lambda *_args, **_kwargs: {"ok": True})

    results = health_check.run_health_checks()
    assert results["ok"] is True
    assert results["chatwoot"]["ok"] is True
    assert results["mysql"]["ok"] is True
