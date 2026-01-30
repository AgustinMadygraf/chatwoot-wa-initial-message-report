from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

TABLE_NAME = "2_inboxes"

CREATE_INBOXES_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id BIGINT PRIMARY KEY,
    account_id BIGINT NOT NULL,
    name VARCHAR(255),
    channel_type VARCHAR(128),
    address VARCHAR(255),
    last_synced_at DATETIME,
    INDEX idx_account_id (account_id),
    INDEX idx_channel_type (channel_type),
    CONSTRAINT fk_inboxes_account
        FOREIGN KEY (account_id) REFERENCES 1_accounts(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
"""


class InboxesRepository:
    def __init__(self, connection, *, account_id: int) -> None:
        self.connection = connection
        self.account_id = account_id

    def ensure_table(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(CREATE_INBOXES_TABLE_SQL)
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ROW_FORMAT=DYNAMIC")

    def list_inboxes(self) -> list[dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    id,
                    account_id,
                    name,
                    channel_type,
                    address,
                    last_synced_at
                FROM {TABLE_NAME}
                ORDER BY id ASC
                """
            )
            return list(cursor.fetchall() or [])

    def upsert_inbox(self, payload: dict[str, Any]) -> None:
        flattened = _flatten_payload(payload, account_id=self.account_id)
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


def _flatten_payload(payload: dict[str, Any], *, account_id: int) -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    channel_type = payload.get("channel_type")
    if isinstance(channel_type, str) and channel_type.startswith("Channel::"):
        channel_type = channel_type.replace("Channel::", "", 1)
    address = payload.get("address")
    if not (isinstance(address, str) and address.strip()):
        address = _choose_address(payload, channel_type=channel_type)
    return {
        "id": payload.get("id"),
        "account_id": account_id,
        "name": payload.get("name"),
        "channel_type": channel_type,
        "address": address.strip() if isinstance(address, str) else address,
        "last_synced_at": now,
    }


def _choose_address(payload: dict[str, Any], *, channel_type: str | None) -> str | None:
    phone = payload.get("phone_number")
    if isinstance(phone, str) and phone.strip():
        return phone.strip()
    email = payload.get("email")
    if isinstance(email, str) and email.strip():
        return email.strip()
    bot_name = payload.get("bot_name")
    if isinstance(bot_name, str) and bot_name.strip():
        return bot_name.strip()
    if channel_type == "WebWidget":
        website_url = payload.get("website_url")
        if isinstance(website_url, str) and website_url.strip():
            return website_url.strip()
    return None
