from __future__ import annotations

from typing import Iterable, Protocol

from application.dto.message_snapshot import MessageSnapshot


class MessageReaderPort(Protocol):
    """Read-only access to messages for reporting use cases."""

    def list_messages(self, limit: int | None = None) -> Iterable[MessageSnapshot]:
        """Return message snapshots for reporting."""
        ...
