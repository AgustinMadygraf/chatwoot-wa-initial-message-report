from typing import Protocol

from src.entities.chatwoot_connection_result import ChatwootConnectionResult


class ConnectionPresenter(Protocol):
    def present(self, result: ChatwootConnectionResult) -> int:
        ...
