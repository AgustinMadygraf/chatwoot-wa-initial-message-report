from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pymysql.err

TABLE_NAME = "3_conversations"

CREATE_CONVERSATIONS_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id BIGINT PRIMARY KEY,
    account_id BIGINT,
    inbox_id BIGINT,
    address VARCHAR(255),
    created_at BIGINT,
    last_activity_at BIGINT,
    last_synced_at DATETIME,
    INDEX idx_account_id (account_id),
    INDEX idx_inbox_id (inbox_id),
    INDEX idx_inbox_created (inbox_id, created_at),
    INDEX idx_account_last_activity (account_id, last_activity_at)
    ,
    INDEX idx_account_inbox_created_synced (account_id, inbox_id, created_at, last_synced_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
"""

BASE_COLUMNS = {
    "id",
    "account_id",
    "inbox_id",
    "address",
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
            self._drop_extra_columns(cursor)
            self._ensure_index(cursor, "idx_account_id", "account_id")
            self._ensure_index(cursor, "idx_inbox_id", "inbox_id")
            self._ensure_index(cursor, "idx_inbox_created", "inbox_id, created_at")
            self._ensure_index(cursor, "idx_account_last_activity", "account_id, last_activity_at")
            self._ensure_index(
                cursor,
                "idx_account_inbox_created_synced",
                "account_id, inbox_id, created_at, last_synced_at",
            )
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
                    account_id,
                    inbox_id,
                    address,
                    created_at,
                    last_activity_at,
                    last_synced_at
                FROM {TABLE_NAME}
                ORDER BY account_id ASC, inbox_id ASC, created_at ASC, last_synced_at ASC
                """
            )
            return list(cursor.fetchall() or [])

    def upsert_conversation(self, payload: dict[str, Any]) -> None:
        flattened = _flatten_payload(payload)

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

def _flatten_payload(payload: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    address = payload.get("address")
    if not (isinstance(address, str) and address.strip()):
        address = _pick_address(payload)
    return {
        "id": payload.get("id"),
        "account_id": payload.get("account_id"),
        "inbox_id": payload.get("inbox_id"),
        "address": address.strip() if isinstance(address, str) else address,
        "created_at": payload.get("created_at"),
        "last_activity_at": payload.get("last_activity_at"),
        "last_synced_at": now,
    }


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
            name = sender.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
    sender = payload.get("sender")
    if isinstance(sender, dict):
        for key in ("phone_number", "email"):
            value = sender.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        name = sender.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    meta_sender_name = payload.get("meta__sender__name")
    if isinstance(meta_sender_name, str) and meta_sender_name.strip():
        return meta_sender_name.strip()
    return None
