from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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

    def _drop_extra_columns(self, cursor) -> None:
        try:
            cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME}")
        except Exception:  # noqa: BLE001
            return
        rows = cursor.fetchall() or []
        existing = {row["Field"] for row in rows}
        extras = sorted(existing - BASE_COLUMNS)
        for column in extras:
            try:
                cursor.execute(f"ALTER TABLE {TABLE_NAME} DROP COLUMN {column}")
            except Exception:  # noqa: BLE001
                pass

    def _ensure_column(self, cursor, name: str, column_type: str) -> None:
        try:
            cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME} LIKE %s", (name,))
            if cursor.fetchone():
                return
        except Exception:  # noqa: BLE001
            return
        try:
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {name} {column_type}")
        except Exception:  # noqa: BLE001
            pass

    def _ensure_index(self, cursor, name: str, column: str) -> None:
        try:
            cursor.execute(f"CREATE INDEX {name} ON {TABLE_NAME} ({column})")
        except Exception:  # noqa: BLE001
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
        except Exception:  # noqa: BLE001
            pass


def _flatten_payload(payload: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    return {
        "id": payload.get("id"),
        "conversation_id": payload.get("conversation_id"),
        "inbox_id": payload.get("inbox_id"),
        "sender_role": payload.get("sender_role"),
        "content": payload.get("content"),
        "created_at": payload.get("created_at"),
        "last_synced_at": now,
    }
