"""
Path: src/entities/chatwoot_contact.py
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatwootContact:
    id: int
    raw: dict[str, Any]
