from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ContactRow:
    id: Any
    name: str
    phone_number: str
    email: str
    created_at: str


@dataclass(frozen=True)
class ChatwootContactsResult:
    ok: bool
    status_code: Optional[int]
    endpoint: str
    detail: str
    contacts: list[ContactRow]
