from __future__ import annotations

from typing import Protocol


class HealthCheckPort(Protocol):
    def check(self) -> dict: ...
