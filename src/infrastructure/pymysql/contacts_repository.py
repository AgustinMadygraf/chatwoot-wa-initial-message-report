from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS contacts (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    phone_number VARCHAR(64),
    email VARCHAR(255),
    identifier VARCHAR(255),
    avatar_url TEXT,
    created_at BIGINT,
    last_activity_at BIGINT,
    custom_attributes JSON,
    additional_attributes JSON,
    inboxes JSON,
    last_synced_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_INBOXES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS contact_inboxes (
    contact_id BIGINT NOT NULL,
    inbox_id BIGINT NOT NULL,
    inbox_name VARCHAR(255),
    channel_type VARCHAR(64),
    provider VARCHAR(64),
    source_id VARCHAR(255),
    PRIMARY KEY (contact_id, inbox_id, source_id),
    INDEX idx_inbox_id (inbox_id),
    INDEX idx_provider (provider),
    INDEX idx_channel_type (channel_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


class ContactsRepository:
    def __init__(self, connection) -> None:
        self.connection = connection

    def ensure_table(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
            cursor.execute(CREATE_INBOXES_TABLE_SQL)
            for column, col_type in (
                ("created_at", "BIGINT"),
                ("last_activity_at", "BIGINT"),
            ):
                try:
                    cursor.execute(
                        f"ALTER TABLE contacts ADD COLUMN {column} {col_type}"
                    )
                except Exception:
                    # Ignore duplicate column errors for existing tables.
                    pass

    def get_last_activity_at(self, contact_id: int) -> Optional[int]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT last_activity_at FROM contacts WHERE id=%s", (contact_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return row.get("last_activity_at")

    def upsert_contact(self, contact: Dict[str, Any]) -> None:
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        payload = {
            "id": contact.get("id"),
            "name": contact.get("name"),
            "phone_number": contact.get("phone_number"),
            "email": contact.get("email"),
            "identifier": contact.get("identifier"),
            "avatar_url": contact.get("avatar_url"),
            "created_at": contact.get("created_at"),
            "last_activity_at": contact.get("last_activity_at"),
            "custom_attributes": json.dumps(contact.get("custom_attributes") or {}),
            "additional_attributes": json.dumps(contact.get("additional_attributes") or {}),
            "inboxes": json.dumps(contact.get("inboxes") or []),
            "last_synced_at": now,
        }
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO contacts (
                    id, name, phone_number, email, identifier, avatar_url,
                    created_at, last_activity_at, custom_attributes, additional_attributes,
                    inboxes, last_synced_at
                ) VALUES (
                    %(id)s, %(name)s, %(phone_number)s, %(email)s, %(identifier)s, %(avatar_url)s,
                    %(created_at)s, %(last_activity_at)s, %(custom_attributes)s, %(additional_attributes)s,
                    %(inboxes)s, %(last_synced_at)s
                )
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name),
                    phone_number=VALUES(phone_number),
                    email=VALUES(email),
                    identifier=VALUES(identifier),
                    avatar_url=VALUES(avatar_url),
                    created_at=VALUES(created_at),
                    last_activity_at=VALUES(last_activity_at),
                    custom_attributes=VALUES(custom_attributes),
                    additional_attributes=VALUES(additional_attributes),
                    inboxes=VALUES(inboxes),
                    last_synced_at=VALUES(last_synced_at)
                """,
                payload,
            )

    def replace_contact_inboxes(self, contact_id: int, contact_inboxes: list[Dict[str, Any]]) -> None:
        rows = []
        for item in contact_inboxes or []:
            inbox = item.get("inbox") or {}
            rows.append(
                {
                    "contact_id": contact_id,
                    "inbox_id": inbox.get("id"),
                    "inbox_name": inbox.get("name"),
                    "channel_type": inbox.get("channel_type"),
                    "provider": inbox.get("provider"),
                    "source_id": item.get("source_id"),
                }
            )
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM contact_inboxes WHERE contact_id=%s", (contact_id,))
            if rows:
                cursor.executemany(
                    """
                    INSERT INTO contact_inboxes (
                        contact_id, inbox_id, inbox_name, channel_type, provider, source_id
                    ) VALUES (
                        %(contact_id)s, %(inbox_id)s, %(inbox_name)s, %(channel_type)s,
                        %(provider)s, %(source_id)s
                    )
                    """,
                    rows,
                )

    def list_contacts(self) -> list[Dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, phone_number, email, identifier, created_at, last_activity_at
                FROM contacts
                ORDER BY last_activity_at IS NULL, last_activity_at DESC, created_at DESC
                """
            )
            return list(cursor.fetchall() or [])

    def list_contacts_by_channel(
        self,
        *,
        inbox_id: Optional[int] = None,
        provider: Optional[str] = None,
        channel_type: Optional[str] = None,
        inbox_name: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        where = []
        params: list[Any] = []
        if inbox_id is not None:
            where.append("ci.inbox_id=%s")
            params.append(inbox_id)
        if provider:
            where.append("ci.provider=%s")
            params.append(provider)
        if channel_type:
            where.append("ci.channel_type=%s")
            params.append(channel_type)
        if inbox_name:
            where.append("ci.inbox_name LIKE %s")
            params.append(f"%{inbox_name}%")
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        sql = f"""
            SELECT
                c.id,
                c.name,
                c.phone_number,
                c.email,
                c.created_at,
                c.last_activity_at,
                ci.inbox_id,
                ci.inbox_name,
                ci.channel_type,
                ci.provider,
                ci.source_id
            FROM contacts c
            JOIN contact_inboxes ci ON ci.contact_id = c.id
            {where_sql}
            ORDER BY c.last_activity_at IS NULL, c.last_activity_at DESC, c.created_at DESC
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall() or [])

    def count_contacts(self) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM contacts")
            row = cursor.fetchone()
            if not row:
                return 0
            return int(row.get("total") or 0)
