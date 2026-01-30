from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

TABLE_NAME = "4_messages"

CREATE_MESSAGES_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id BIGINT PRIMARY KEY,
    conversation_id BIGINT,
    inbox_id BIGINT,
    message_type INT,
    content_type VARCHAR(64),
    status VARCHAR(64),
    sender_type VARCHAR(64),
    sender_id BIGINT,
    content TEXT,
    created_at BIGINT,
    last_synced_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
"""

BASE_COLUMNS = {
    "id",
    "conversation_id",
    "inbox_id",
    "message_type",
    "content_type",
    "status",
    "sender_type",
    "sender_id",
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
            self._downgrade_dynamic_varchars(cursor)

    def list_messages(self) -> list[dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    id,
                    conversation_id,
                    inbox_id,
                    message_type,
                    sender_type,
                    sender__name,
                    created_at,
                    content
                FROM {TABLE_NAME}
                ORDER BY id DESC
                """
            )
            return list(cursor.fetchall() or [])

    def upsert_message(self, payload: dict[str, Any]) -> None:
        flattened, dynamic_columns = _flatten_payload(payload)
        if dynamic_columns:
            self._ensure_columns(dynamic_columns)

        columns = list(flattened.keys())
        insert_cols = ", ".join(columns)
        placeholders = ", ".join([f"%({col})s" for col in columns])
        update_cols = ", ".join([f"{col}=VALUES({col})" for col in columns if col != "id"])
        sql = f"""
            INSERT INTO {TABLE_NAME} ({insert_cols})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_cols}
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, flattened)

    def _ensure_columns(self, columns: dict[str, str]) -> None:
        existing = self._get_existing_columns()
        with self.connection.cursor() as cursor:
            for column, col_type in columns.items():
                if column in existing:
                    continue
                cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {column} {col_type}")

    def _get_existing_columns(self) -> set[str]:
        with self.connection.cursor() as cursor:
            cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME}")
            rows = cursor.fetchall() or []
            return {row["Field"] for row in rows}

    def _downgrade_dynamic_varchars(self, cursor) -> None:
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
            """,
            (TABLE_NAME,),
        )
        rows = cursor.fetchall() or []
        for row in rows:
            name = row.get("COLUMN_NAME")
            data_type = (row.get("DATA_TYPE") or "").lower()
            if not name or name in BASE_COLUMNS:
                continue
            if data_type in {"varchar", "char"}:
                cursor.execute(f"ALTER TABLE {TABLE_NAME} MODIFY COLUMN {name} TEXT")


def _flatten_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    flattened: dict[str, Any] = {
        "id": payload.get("id"),
        "conversation_id": payload.get("conversation_id"),
        "inbox_id": payload.get("inbox_id"),
        "message_type": payload.get("message_type"),
        "content_type": payload.get("content_type"),
        "status": payload.get("status"),
        "sender_type": payload.get("sender_type"),
        "sender_id": payload.get("sender_id"),
        "content": payload.get("content"),
        "created_at": payload.get("created_at"),
        "last_synced_at": now,
    }
    dynamic_columns: dict[str, str] = {}
    _flatten_value("", payload, flattened, dynamic_columns)
    return flattened, dynamic_columns


def _flatten_value(
    prefix: str,
    value: Any,
    out: dict[str, Any],
    types: dict[str, str],
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            next_prefix = _join_prefix(prefix, key)
            _flatten_value(next_prefix, item, out, types)
        return

    if isinstance(value, list):
        if all(isinstance(item, dict) for item in value):
            for idx, item in enumerate(value):
                next_prefix = _join_prefix(prefix, str(idx))
                _flatten_value(next_prefix, item, out, types)
            return
        column = _safe_column(prefix)
        csv_value = ",".join(str(item) for item in value)
        out[column] = csv_value
        types[column] = "TEXT"
        return

    column = _safe_column(prefix)
    out[column] = _normalize_scalar(value)
    types[column] = _infer_column_type(value)


def _join_prefix(prefix: str, key: str) -> str:
    if not prefix:
        return str(key)
    return f"{prefix}__{key}"


def _safe_column(name: str) -> str:
    base = re.sub(r"[^0-9a-zA-Z_]+", "_", name).strip("_").lower()
    if not base:
        base = "field"
    if len(base) <= 60:
        return base
    digest = hashlib.md5(base.encode("utf-8")).hexdigest()[:8]
    return f"{base[:51]}_{digest}"


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return 1 if value else 0
    if value is None or isinstance(value, (int, float, str)):
        return value
    return str(value)


def _infer_column_type(value: Any) -> str:
    if isinstance(value, bool):
        return "TINYINT(1)"
    if isinstance(value, int):
        return "BIGINT"
    if isinstance(value, float):
        return "DOUBLE"
    return "TEXT"
