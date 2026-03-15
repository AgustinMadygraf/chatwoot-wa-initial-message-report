"""
Path: src/interface_adapter/controllers/fastapi_proxy_controllers.py
"""

from typing import Any

from src.use_case.gateways.chatwoot_proxy_gateway import ChatwootProxyGateway


class GetInboxesController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    async def run(self, account_id: int) -> Any:
        self._client.enforce_account_id(account_id)
        return await self._client.get_inboxes(account_id)


class GetInboxByIdController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    async def run(self, account_id: int, inbox_id: int) -> dict[str, Any]:
        self._client.enforce_account_id(account_id)
        return await self._client.get_inbox_by_id(account_id=account_id, inbox_id=inbox_id)


class GetContactsController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    async def run(self, account_id: int, page: str | None) -> dict[str, Any]:
        self._client.enforce_account_id(account_id)
        return await self._client.get_contacts(account_id=account_id, page=page)


class GetContactByIdController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    async def run(self, account_id: int, contact_id: int) -> dict[str, Any]:
        self._client.enforce_account_id(account_id)
        return await self._client.get_contact_by_id(account_id=account_id, contact_id=contact_id)


class GetConversationsController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    async def run(
        self,
        account_id: int,
        page: str | None,
        status: str | None,
        inbox_id: int | None,
    ) -> dict[str, Any]:
        self._client.enforce_account_id(account_id)
        return await self._client.get_conversations(
            account_id=account_id,
            page=page,
            status=status,
            inbox_id=inbox_id,
        )


class GetConversationByIdController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    async def run(self, account_id: int, conversation_id: int) -> dict[str, Any]:
        self._client.enforce_account_id(account_id)
        return await self._client.get_conversation_by_id(
            account_id=account_id,
            conversation_id=conversation_id,
        )


__all__ = [
    "GetInboxesController",
    "GetInboxByIdController",
    "GetContactsController",
    "GetContactByIdController",
    "GetConversationsController",
    "GetConversationByIdController",
]
