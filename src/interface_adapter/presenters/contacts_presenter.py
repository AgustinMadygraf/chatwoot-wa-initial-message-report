from typing import Protocol

from src.entities.chatwoot_contacts_result import ChatwootContactsResult


class ContactsPresenter(Protocol):
    def present(self, result: ChatwootContactsResult) -> int:
        ...
