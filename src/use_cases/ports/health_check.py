from __future__ import annotations

from typing import Protocol, TypedDict


class HealthServiceStatus(TypedDict):
    ok: bool
    error: str | None


class HealthCheckResults(TypedDict):
    ok: bool
    chatwoot: HealthServiceStatus
    mysql: HealthServiceStatus


class HealthCheckPort(Protocol):
    def check(self) -> HealthCheckResults: ...
