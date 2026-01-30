from __future__ import annotations

from typing import Any

from entities.mysql_config import MySQLConfig
from infrastructure.pymysql.mysql_admin_gateway import PyMySQLAdminGateway


class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, Any]] = []

    def execute(self, sql: str, params: Any = None) -> None:
        self.executed.append((sql, params))

    def fetchone(self) -> dict[str, Any] | None:
        return {"ok": 1}

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_obj = FakeCursor()
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self.cursor_obj

    def close(self) -> None:
        self.closed = True


def test_mysql_admin_gateway_create_and_check(monkeypatch) -> None:
    fake_conn = FakeConnection()
    monkeypatch.setattr(
        "infrastructure.pymysql.mysql_admin_gateway.pymysql.connect",
        lambda **_kwargs: fake_conn,
    )
    gateway = PyMySQLAdminGateway()
    config = MySQLConfig(host="h", user="u", password="p", database="d")
    gateway.create_database(config)
    gateway.check_connection(config)
    assert fake_conn.closed is True
    assert fake_conn.cursor_obj.executed
