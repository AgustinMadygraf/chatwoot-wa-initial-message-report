from __future__ import annotations

from typing import Iterable

from application.dto.message_snapshot import MessageSnapshot
from application.ports.message_reader import MessageReaderPort
from infrastructure.pymysql.messages_repository import MessagesRepository


class MySQLMessageReader(MessageReaderPort):
    """Adapter that exposes message snapshots from MySQL."""

    def __init__(self, connection, *, ensure_table: bool = True) -> None:
        self._repo = MessagesRepository(connection)
        self._ensure_table = ensure_table

    def list_messages(self, limit: int | None = None) -> Iterable[MessageSnapshot]:
        if self._ensure_table:
            self._repo.ensure_table()
        for row in self._repo.list_messages(limit=limit):
            content = row.get("content") or ""
            conversation_id = row.get("conversation_id")
            created_at = row.get("created_at")
            yield MessageSnapshot(
                content=str(content),
                conversation_id=conversation_id,
                created_at=created_at,
            )
