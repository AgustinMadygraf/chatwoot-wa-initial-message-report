"""
Path: src/use_case/gateways/chatwoot_proxy_gateway.py
"""

from typing import Any, Protocol


class ChatwootProxyGateway(Protocol):
    def enforce_account_id(self, account_id: int) -> None:
        ...

    async def get_inboxes(self, account_id: int) -> Any:
        ...

    async def get_inbox_by_id(self, account_id: int, inbox_id: int) -> dict[str, Any]:
        ...

    async def get_contacts(self, account_id: int, page: str | None) -> dict[str, Any]:
        ...

    async def get_contact_by_id(self, account_id: int, contact_id: int) -> dict[str, Any]:
        ...

    async def get_conversations(
        self,
        account_id: int,
        page: str | None,
        status: str | None,
        inbox_id: int | None,
    ) -> dict[str, Any]:
        ...

    async def get_conversation_by_id(
        self,
        account_id: int,
        conversation_id: int,
    ) -> dict[str, Any]:
        ...

    async def get_conversation_messages(
        self,
        account_id: int,
        conversation_id: int,
        page: str | None,
    ) -> dict[str, Any]:
        ...
