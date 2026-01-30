from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Account:
    id: int | None
    name: str | None
    locale: str | None
    status: str | None
    created_at: str | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Account":
        return cls(
            id=_as_int(payload.get("id")),
            name=_as_str(payload.get("name")),
            locale=_as_str(payload.get("locale")),
            status=_as_str(payload.get("status")),
            created_at=_as_str(payload.get("created_at")),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "locale": self.locale,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class Inbox:
    id: int | None
    account_id: int | None
    name: str | None
    channel_type: str | None
    address: str | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Inbox":
        return cls(
            id=_as_int(payload.get("id")),
            account_id=_as_int(payload.get("account_id")),
            name=_as_str(payload.get("name")),
            channel_type=_as_str(payload.get("channel_type")),
            address=_pick_address(payload),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "name": self.name,
            "channel_type": self.channel_type,
            "address": self.address,
        }


@dataclass(frozen=True)
class Conversation:
    id: int | None
    account_id: int | None
    inbox_id: int | None
    status: str | None
    created_at: int | None
    last_activity_at: int | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Conversation":
        return cls(
            id=_as_int(payload.get("id")),
            account_id=_as_int(payload.get("account_id")),
            inbox_id=_as_int(payload.get("inbox_id")),
            status=_as_str(payload.get("status")),
            created_at=_as_int(payload.get("created_at")),
            last_activity_at=_as_int(payload.get("last_activity_at")),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "inbox_id": self.inbox_id,
            "status": self.status,
            "created_at": self.created_at,
            "last_activity_at": self.last_activity_at,
        }


@dataclass(frozen=True)
class Message:
    id: int | None
    conversation_id: int | None
    inbox_id: int | None
    message_type: int | None
    sender_type: str | None
    sender_id: int | None
    sender_role: str | None
    content: str | None
    created_at: int | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Message":
        sender_type = _as_str(payload.get("sender_type"))
        message_type = _as_int(payload.get("message_type"))
        return cls(
            id=_as_int(payload.get("id")),
            conversation_id=_as_int(payload.get("conversation_id")),
            inbox_id=_as_int(payload.get("inbox_id")),
            message_type=message_type,
            sender_type=sender_type,
            sender_id=_as_int(payload.get("sender_id")),
            sender_role=_derive_sender_role(sender_type, message_type),
            content=_as_str(payload.get("content")),
            created_at=_as_int(payload.get("created_at")),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "inbox_id": self.inbox_id,
            "message_type": self.message_type,
            "sender_type": self.sender_type,
            "sender_id": self.sender_id,
            "sender_role": self.sender_role,
            "content": self.content,
            "created_at": self.created_at,
        }


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _pick_address(payload: dict[str, Any]) -> str | None:
    for key in ("phone_number", "email", "bot_name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    channel_type = payload.get("channel_type")
    if isinstance(channel_type, str) and channel_type.endswith("WebWidget"):
        website_url = payload.get("website_url")
        if isinstance(website_url, str) and website_url.strip():
            return website_url.strip()
    return None


def _derive_sender_role(sender_type: str | None, message_type: int | None) -> str | None:
    if sender_type:
        lowered = sender_type.lower()
        if lowered == "user":
            return "agent"
        if lowered == "contact":
            return "contact"
    if message_type == 1:
        return "agent"
    if message_type == 0:
        return "contact"
    return None
