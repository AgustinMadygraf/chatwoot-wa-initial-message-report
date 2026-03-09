"""
Path: src/interface_adapter/controllers/fastapi_proxy_controllers.py
"""

from typing import Any

from src.use_case.gateways.chatwoot_proxy_gateway import ChatwootProxyGateway


class GetInboxesController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    def run(self, account_id: int) -> Any:
        self._client.enforce_account_id(account_id)
        return self._client.get_inboxes(account_id)


class GetInboxByIdController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    def run(self, account_id: int, inbox_id: int) -> dict[str, Any]:
        self._client.enforce_account_id(account_id)
        return self._client.get_inbox_by_id(account_id=account_id, inbox_id=inbox_id)


class GetContactsController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    def run(self, account_id: int, page: str | None) -> dict[str, Any]:
        self._client.enforce_account_id(account_id)
        return self._client.get_contacts(account_id=account_id, page=page)


class GetContactByIdController:
    def __init__(self, client: ChatwootProxyGateway) -> None:
        self._client = client

    def run(self, account_id: int, contact_id: int) -> dict[str, Any]:
        self._client.enforce_account_id(account_id)
        return self._client.get_contact_by_id(account_id=account_id, contact_id=contact_id)


__all__ = [
    "GetInboxesController",
    "GetInboxByIdController",
    "GetContactsController",
    "GetContactByIdController",
]
