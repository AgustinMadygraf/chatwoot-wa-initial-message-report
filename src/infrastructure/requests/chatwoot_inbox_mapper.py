"""
Path: src/infrastructure/requests/chatwoot_inbox_mapper.py
"""

from typing import Any

from src.entities.chatwoot_inbox import ChatwootInbox


def map_to_inbox(value: dict[str, Any]) -> ChatwootInbox:
    return ChatwootInbox(
        id=_safe_int(value.get("id"), -1),
        name=str(value.get("name") or ""),
        channel_type=str(value.get("channel_type") or ""),
        channel_id=_safe_int_or_none(value.get("channel_id")),
        raw=value,
    )


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
