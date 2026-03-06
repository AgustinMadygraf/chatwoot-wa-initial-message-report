from typing import Protocol

from src.entities.chatwoot_connection_result import ChatwootConnectionResult
from src.entities.chatwoot_contacts_result import ChatwootContactsResult


class ChatwootApiGateway(Protocol):
    def validate_connection(self) -> ChatwootConnectionResult:
        ...

    def fetch_contacts_page(self) -> ChatwootContactsResult:
        ...
