from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MessageSnapshot:
    """Minimal message data needed for intent coverage analysis."""

    content: str
    conversation_id: int | None
    created_at: int | None = None
