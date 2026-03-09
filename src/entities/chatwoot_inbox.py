"""
Path: src/entities/chatwoot_inbox.py
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatwootInbox:
    id: int
    name: str
    channel_type: str
    channel_id: int | None
    raw: dict[str, Any]
