from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

TABLE_NAME = "3_conversations"

CREATE_CONVERSATIONS_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id BIGINT PRIMARY KEY,
    account_id BIGINT,
    inbox_id BIGINT,
    address VARCHAR(255),
    status VARCHAR(64),
    created_at BIGINT,
    last_activity_at BIGINT,
    last_synced_at DATETIME,
    INDEX idx_account_id (account_id),
    INDEX idx_inbox_id (inbox_id),
    CONSTRAINT fk_conversations_account
        FOREIGN KEY (account_id) REFERENCES 1_accounts(id),
    CONSTRAINT fk_conversations_inbox
        FOREIGN KEY (inbox_id) REFERENCES 2_inboxes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
"""

BASE_COLUMNS = {
    "id",
    "account_id",
    "inbox_id",
    "address",
    "status",
    "created_at",
    "last_activity_at",
    "last_synced_at",
}


class ConversationsRepository:
    def __init__(self, connection) -> None:
        self.connection = connection

    def ensure_table(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(CREATE_CONVERSATIONS_TABLE_SQL)
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ROW_FORMAT=DYNAMIC")
            self._downgrade_dynamic_varchars(cursor)
            try:
                cursor.execute(
                    f"ALTER TABLE {TABLE_NAME} ADD COLUMN address VARCHAR(255)"
                )
            except Exception:
                pass
            self._ensure_index(cursor, "idx_account_id", "account_id")
            self._ensure_index(cursor, "idx_inbox_id", "inbox_id")
            self._ensure_fk(
                cursor,
                "fk_conversations_account",
                "account_id",
                "1_accounts",
                "id",
            )
            self._ensure_fk(
                cursor,
                "fk_conversations_inbox",
                "inbox_id",
                "2_inboxes",
                "id",
            )

    def list_conversations(self) -> list[dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    id,
                    inbox_id,
                    status,
                    address,
                    created_at,
                    last_activity_at,
                    meta__sender__id,
                    meta__sender__name
                FROM {TABLE_NAME}
                ORDER BY id DESC
                """
            )
            return list(cursor.fetchall() or [])

    def upsert_conversation(self, payload: dict[str, Any]) -> None:
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

    def _ensure_index(self, cursor, name: str, column: str) -> None:
        try:
            cursor.execute(f"CREATE INDEX {name} ON {TABLE_NAME} ({column})")
        except Exception:
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
        except Exception:
            pass

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
    address = payload.get("address")
    if not (isinstance(address, str) and address.strip()):
        address = _pick_address(payload)
    flattened: dict[str, Any] = {
        "id": payload.get("id"),
        "account_id": payload.get("account_id"),
        "inbox_id": payload.get("inbox_id"),
        "address": address.strip() if isinstance(address, str) else address,
        "status": payload.get("status"),
        "created_at": payload.get("created_at"),
        "last_activity_at": payload.get("last_activity_at"),
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


def _pick_address(payload: dict[str, Any]) -> str | None:
    for key in ("phone_number", "email"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    meta = payload.get("meta")
    if isinstance(meta, dict):
        sender = meta.get("sender")
        if isinstance(sender, dict):
            for key in ("phone_number", "email"):
                value = sender.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    sender = payload.get("sender")
    if isinstance(sender, dict):
        for key in ("phone_number", "email"):
            value = sender.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None
