from __future__ import annotations

from typing import Any

import infrastructure.pymysql.health as mysql_connection
import infrastructure.pymysql.connection as pymysql_connection
from infrastructure.pymysql.unit_of_work import PyMySQLUnitOfWork


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
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> FakeCursor:
        return self.cursor_obj

    def close(self) -> None:
        self.closed = True

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_check_connection_success(monkeypatch) -> None:
    fake_conn = FakeConnection()
    monkeypatch.setattr(mysql_connection.pymysql, "connect", lambda **_kwargs: fake_conn)
    config = mysql_connection.MySQLConfig(host="h", user="u", password="p", database="d")
    result = mysql_connection.check_connection(config)
    assert result["ok"] is True
    assert fake_conn.closed is True


def test_check_connection_failure(monkeypatch) -> None:
    def _raise(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(mysql_connection.pymysql, "connect", _raise)
    config = mysql_connection.MySQLConfig(host="h", user="u", password="p", database="d")
    result = mysql_connection.check_connection(config)
    assert result["ok"] is False
    assert "boom" in result["error"]


def test_get_mysql_connection(monkeypatch) -> None:
    sentinel = object()
    captured: dict[str, Any] = {}

    def _connect(**kwargs):
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(pymysql_connection.pymysql, "connect", _connect)
    config = pymysql_connection.MySQLConfig(host="h", user="u", password="p", database="d")
    conn = pymysql_connection.get_mysql_connection(config)
    assert conn is sentinel
    assert captured["host"] == "h"


def test_unit_of_work_commit(monkeypatch) -> None:
    fake_conn = FakeConnection()
    monkeypatch.setattr(
        "infrastructure.pymysql.unit_of_work.get_mysql_connection",
        lambda *_args, **_kwargs: fake_conn,
    )
    config = pymysql_connection.MySQLConfig(host="h", user="u", password="p", database="d")
    with PyMySQLUnitOfWork(config) as uow:
        assert uow.connection is fake_conn
