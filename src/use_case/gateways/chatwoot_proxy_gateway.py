"""
Path: src/use_case/gateways/chatwoot_proxy_gateway.py
"""

from typing import Any, Protocol

class ChatwootProxyGateway(Protocol):
    def enforce_account_id(self, account_id: int) -> None:
        ...

    def get_inboxes(self, account_id: int) -> Any:
        ...

    def get_inbox_by_id(self, account_id: int, inbox_id: int) -> dict[str, Any]:
        ...

    def get_contacts(self, account_id: int, page: str | None) -> dict[str, Any]:
        ...

    def get_contact_by_id(self, account_id: int, contact_id: int) -> dict[str, Any]:
        ...
