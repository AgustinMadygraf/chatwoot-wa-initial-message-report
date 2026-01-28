from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MySQLConfig:
    host: str
    user: str
    password: str
    database: str
    port: int = 3306
    connect_timeout: int = 5
