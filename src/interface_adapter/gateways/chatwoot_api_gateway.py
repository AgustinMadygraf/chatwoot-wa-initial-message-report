from typing import Protocol

from src.entities.chatwoot_connection_result import ChatwootConnectionResult


class ChatwootApiGateway(Protocol):
    def validate_connection(self) -> ChatwootConnectionResult:
        ...
