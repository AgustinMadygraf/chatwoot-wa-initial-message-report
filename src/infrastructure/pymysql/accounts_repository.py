from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


TABLE_NAME = "1_accounts"

CREATE_ACCOUNTS_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    locale VARCHAR(32),
    status VARCHAR(64),
    created_at DATETIME,
    last_synced_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


class AccountsRepository:
    def __init__(self, connection) -> None:
        self.connection = connection

    def ensure_table(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(CREATE_ACCOUNTS_TABLE_SQL)

    def list_accounts(self) -> list[Dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    id,
                    name,
                    locale,
                    status,
                    created_at,
                FROM {TABLE_NAME}
                ORDER BY id ASC
                """
            )
            return list(cursor.fetchall() or [])

    def upsert_account(self, payload: Dict[str, Any]) -> None:
        flattened = self._flatten_payload(payload)
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
    def _flatten_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        created_at = _parse_iso_datetime(payload.get("created_at"))
        return {
            "id": payload.get("id"),
            "name": payload.get("name"),
            "locale": payload.get("locale"),
            "status": payload.get("status"),
            "created_at": created_at,
            "last_synced_at": now,
        }


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None
