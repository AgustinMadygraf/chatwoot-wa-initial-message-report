from __future__ import annotations

from typing import Any, Protocol


class ChatwootClientPort(Protocol):
    def list_inboxes(self) -> dict[str, Any]: ...

    def list_conversations(
        self, *, page: int, per_page: int | None = None, status: str = "all"
    ) -> dict[str, Any]: ...

    def list_conversation_messages(
        self, *, conversation_id: int, page: int, per_page: int | None = None
    ) -> dict[str, Any]: ...

    def check_connection(self) -> dict[str, Any]: ...

    def get_account_details(self) -> dict[str, Any]: ...
