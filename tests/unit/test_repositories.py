from __future__ import annotations

from typing import Any

from infrastructure.pymysql import accounts_repository as accounts
from infrastructure.pymysql import conversations_repository as conversations
from infrastructure.pymysql import inboxes_repository as inboxes
from infrastructure.pymysql import messages_repository as messages


class FakeCursor:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []
        self.executed: list[tuple[str, Any]] = []

    def execute(self, sql: str, params: Any = None) -> None:
        self.executed.append((sql, params))

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self.rows)

    def fetchone(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class FakeConnection:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.cursor_obj = FakeCursor(rows=rows)

    def cursor(self) -> FakeCursor:
        return self.cursor_obj

    def close(self) -> None:
        return None


def test_accounts_repository_parse_iso() -> None:
    dt = accounts._parse_iso_datetime("2024-01-01T00:00:00Z")
    assert dt is not None


def test_accounts_repository_upsert_executes_sql() -> None:
    conn = FakeConnection()
    repo = accounts.AccountsRepository(conn)
    repo.ensure_table()
    repo.upsert_account({"id": 1, "name": "A"})
    assert conn.cursor_obj.executed


def test_inboxes_flatten_payload_address_priority() -> None:
    payload = {"phone_number": " 123 ", "email": "x@y", "bot_name": "bot"}
    flattened = inboxes._flatten_payload(payload, account_id=5)
    assert flattened["address"] == "123"
    payload = {"email": "x@y", "bot_name": "bot"}
    flattened = inboxes._flatten_payload(payload, account_id=5)
    assert flattened["address"] == "x@y"


def test_inboxes_repository_upsert_executes_sql() -> None:
    conn = FakeConnection()
    repo = inboxes.InboxesRepository(conn, account_id=1)
    repo.ensure_table()
    repo.upsert_inbox({"id": 2, "name": "Inbox"})
    assert conn.cursor_obj.executed


def test_conversations_flatten_and_safe_column() -> None:
    payload = {"id": 1, "meta": {"sender": {"name": "Ana"}}, "tags": ["a", "b"]}
    flattened, dynamic = conversations._flatten_payload(payload)
    assert "meta__sender__name" in flattened
    assert "tags" in flattened
    assert dynamic
    assert conversations._safe_column("%%%") == "field"


def test_conversations_repository_upsert_executes_sql() -> None:
    conn = FakeConnection(rows=[{"Field": "id"}])
    repo = conversations.ConversationsRepository(conn)
    repo.ensure_table()
    repo.upsert_conversation({"id": 9, "status": "open"})
    assert conn.cursor_obj.executed


def test_messages_flatten_and_types() -> None:
    payload = {"id": 1, "sender": {"name": "Ana"}, "flags": [1, 2]}
    flattened, dynamic = messages._flatten_payload(payload)
    assert "sender__name" in flattened
    assert "flags" in flattened
    assert dynamic


def test_messages_repository_upsert_executes_sql() -> None:
    conn = FakeConnection(rows=[{"Field": "id"}])
    repo = messages.MessagesRepository(conn)
    repo.ensure_table()
    repo.upsert_message({"id": 3, "content": "hi"})
    assert conn.cursor_obj.executed
