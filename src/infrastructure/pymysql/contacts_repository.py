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


class ContactsRepository:
    def __init__(self, connection) -> None:
        self.connection = connection

    def ensure_table(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
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

    def count_contacts(self) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM contacts")
            row = cursor.fetchone()
            if not row:
                return 0
            return int(row.get("total") or 0)
