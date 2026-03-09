"""
Path: src/infrastructure/requests/inboxes_payload_mapper.py
"""

from typing import Any


def normalize_inboxes_payload(payload: Any) -> list[dict[str, Any]] | None:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        nested = payload.get("payload")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
    return None
