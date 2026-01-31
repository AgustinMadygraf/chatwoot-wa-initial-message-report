from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any

import pymysql.err

TABLE_NAME = "4_messages"

CREATE_MESSAGES_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id BIGINT PRIMARY KEY,
    conversation_id BIGINT,
    inbox_id BIGINT,
    sender_role VARCHAR(16),
    content TEXT,
    created_at BIGINT,
    last_synced_at DATETIME,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_inbox_id (inbox_id),
    INDEX idx_conversation_created (conversation_id, created_at),
    INDEX idx_inbox_created (inbox_id, created_at),
    INDEX idx_inbox_conversation_created_synced (inbox_id, conversation_id, created_at, last_synced_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
"""

BASE_COLUMNS = {
    "id",
    "conversation_id",
    "inbox_id",
    "sender_role",
    "content",
    "created_at",
    "last_synced_at",
}


class MessagesRepository:
    def __init__(self, connection) -> None:
        self.connection = connection

    def ensure_table(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(CREATE_MESSAGES_TABLE_SQL)
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ROW_FORMAT=DYNAMIC")
            self._drop_extra_columns(cursor)
            self._ensure_column(cursor, "sender_role", "VARCHAR(16)")
            self._ensure_index(cursor, "idx_conversation_id", "conversation_id")
            self._ensure_index(cursor, "idx_inbox_id", "inbox_id")
            self._ensure_index(cursor, "idx_conversation_created", "conversation_id, created_at")
            self._ensure_index(cursor, "idx_inbox_created", "inbox_id, created_at")
            self._ensure_index(
                cursor,
                "idx_inbox_conversation_created_synced",
                "inbox_id, conversation_id, created_at, last_synced_at",
            )
            self._ensure_fk(
                cursor,
                "fk_messages_conversation",
                "conversation_id",
                "3_conversations",
                "id",
            )
            self._ensure_fk(
                cursor,
                "fk_messages_inbox",
                "inbox_id",
                "2_inboxes",
                "id",
            )

    def list_messages(self) -> list[dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    id,
                    conversation_id,
                    inbox_id,
                    sender_role,
                    created_at,
                    content
                FROM {TABLE_NAME}
                ORDER BY inbox_id ASC, conversation_id ASC, created_at ASC, last_synced_at ASC
                """
            )
            return list(cursor.fetchall() or [])

    def upsert_message(self, payload: dict[str, Any]) -> None:
        flattened, _dynamic = _flatten_payload(payload)
        record = {key: flattened[key] for key in BASE_COLUMNS if key in flattened}

        columns = list(record.keys())
        insert_cols = ", ".join(columns)
        placeholders = ", ".join([f"%({col})s" for col in columns])
        update_cols = ", ".join([f"{col}=VALUES({col})" for col in columns if col != "id"])
        sql = f"""
            INSERT INTO {TABLE_NAME} ({insert_cols})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_cols}
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, record)

    def _drop_extra_columns(self, cursor) -> None:
        try:
            cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME}")
        except pymysql.err.OperationalError:
            return
        rows = cursor.fetchall() or []
        existing = {row["Field"] for row in rows}
        extras = sorted(existing - BASE_COLUMNS)
        for column in extras:
            try:
                cursor.execute(f"ALTER TABLE {TABLE_NAME} DROP COLUMN {column}")
            except pymysql.err.OperationalError:
                pass

    def _ensure_column(self, cursor, name: str, column_type: str) -> None:
        try:
            cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME} LIKE %s", (name,))
            if cursor.fetchone():
                return
        except pymysql.err.OperationalError:
            return
        try:
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {name} {column_type}")
        except pymysql.err.OperationalError:
            pass

    def _ensure_index(self, cursor, name: str, column: str) -> None:
        try:
            cursor.execute(f"CREATE INDEX {name} ON {TABLE_NAME} ({column})")
        except pymysql.err.OperationalError:
            pass

    def _ensure_fk(
        self,
        cursor,
        name: str,
        column: str,
        ref_table: str,
        ref_column: str,
    ) -> None:
        try:
            cursor.execute(
                f"ALTER TABLE {TABLE_NAME} "
                f"ADD CONSTRAINT {name} FOREIGN KEY ({column}) "
                f"REFERENCES {ref_table}({ref_column})"
            )
        except pymysql.err.OperationalError:
            pass


def _flatten_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    base = {
        "id": payload.get("id"),
        "conversation_id": payload.get("conversation_id"),
        "inbox_id": payload.get("inbox_id"),
        "sender_role": payload.get("sender_role"),
        "content": payload.get("content"),
        "created_at": payload.get("created_at"),
        "last_synced_at": now,
    }
    dynamic = _flatten_dynamic(payload, exclude=BASE_COLUMNS)
    flattened = {**base, **dynamic}
    return flattened, dynamic


def _flatten_dynamic(payload: dict[str, Any], *, exclude: set[str]) -> dict[str, Any]:
    dynamic: dict[str, Any] = {}

    def visit(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                visit(_join_key(prefix, key), nested)
            return
        column = _safe_column(prefix)
        if column in exclude:
            return
        dynamic[column] = _stringify_value(value)

    for key, value in payload.items():
        if key in exclude:
            continue
        visit(str(key), value)

    return dynamic


def _join_key(prefix: str, key: Any) -> str:
    if not prefix:
        return str(key)
    return f"{prefix}__{key}"


def _stringify_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=True)
        except (TypeError, ValueError):
            return str(value)
    return value


def _safe_column(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", value).strip("_")
    if not safe:
        return "field"
    if safe[0].isdigit():
        safe = f"field_{safe}"
    return safe.lower()
