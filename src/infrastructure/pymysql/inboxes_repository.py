from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

CREATE_INBOXES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS inboxes (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    channel_id BIGINT,
    channel_type VARCHAR(128),
    provider VARCHAR(128),
    phone_number VARCHAR(64),
    email VARCHAR(255),
    website_url TEXT,
    website_token VARCHAR(255),
    last_synced_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
"""

BASE_COLUMNS = {
    "id",
    "name",
    "channel_id",
    "channel_type",
    "provider",
    "phone_number",
    "email",
    "website_url",
    "website_token",
    "last_synced_at",
}


class InboxesRepository:
    def __init__(self, connection) -> None:
        self.connection = connection

    def ensure_table(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(CREATE_INBOXES_TABLE_SQL)
            cursor.execute("ALTER TABLE inboxes ROW_FORMAT=DYNAMIC")
            self._downgrade_dynamic_varchars(cursor)

    def list_inboxes(self) -> list[Dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    channel_id,
                    channel_type,
                    provider,
                    phone_number,
                    email,
                    website_url,
                    website_token
                FROM inboxes
                ORDER BY id ASC
                """
            )
            return list(cursor.fetchall() or [])

    def upsert_inbox(self, payload: Dict[str, Any]) -> None:
        flattened, dynamic_columns = _flatten_payload(payload)
        if dynamic_columns:
            self._ensure_columns(dynamic_columns)

        columns = list(flattened.keys())
        insert_cols = ", ".join(columns)
        placeholders = ", ".join([f"%({col})s" for col in columns])
        update_cols = ", ".join([f"{col}=VALUES({col})" for col in columns if col != "id"])
        sql = f"""
            INSERT INTO inboxes ({insert_cols})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_cols}
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, flattened)

    def _ensure_columns(self, columns: Dict[str, str]) -> None:
        existing = self._get_existing_columns()
        with self.connection.cursor() as cursor:
            for column, col_type in columns.items():
                if column in existing:
                    continue
                cursor.execute(f"ALTER TABLE inboxes ADD COLUMN {column} {col_type}")

    def _get_existing_columns(self) -> set[str]:
        with self.connection.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM inboxes")
            rows = cursor.fetchall() or []
            return {row["Field"] for row in rows}

    def _downgrade_dynamic_varchars(self, cursor) -> None:
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'inboxes'
            """
        )
        rows = cursor.fetchall() or []
        for row in rows:
            name = row.get("COLUMN_NAME")
            data_type = (row.get("DATA_TYPE") or "").lower()
            if not name or name in BASE_COLUMNS:
                continue
            if data_type in {"varchar", "char"}:
                cursor.execute(f"ALTER TABLE inboxes MODIFY COLUMN {name} TEXT")


def _flatten_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    flattened: Dict[str, Any] = {
        "id": payload.get("id"),
        "name": payload.get("name"),
        "channel_id": payload.get("channel_id"),
        "channel_type": payload.get("channel_type"),
        "provider": payload.get("provider"),
        "phone_number": payload.get("phone_number"),
        "email": payload.get("email"),
        "website_url": payload.get("website_url"),
        "website_token": payload.get("website_token"),
        "last_synced_at": now,
    }
    dynamic_columns: Dict[str, str] = {}
    _flatten_value("", payload, flattened, dynamic_columns)
    return flattened, dynamic_columns


def _flatten_value(
    prefix: str,
    value: Any,
    out: Dict[str, Any],
    types: Dict[str, str],
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
        # list of scalars -> CSV
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
