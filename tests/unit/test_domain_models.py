from __future__ import annotations

from domain.chatwoot import Account, Conversation, Inbox, Message


def test_account_from_payload() -> None:
    model = Account.from_payload({"id": "1", "name": "A", "locale": "es"})
    assert model.id == 1
    assert model.name == "A"
    assert model.to_record()["id"] == 1


def test_inbox_from_payload_address() -> None:
    model = Inbox.from_payload({"id": 2, "phone_number": " 123 "})
    assert model.address == "123"


def test_conversation_from_payload() -> None:
    model = Conversation.from_payload({"id": "10", "created_at": "5"})
    assert model.id == 10
    assert model.created_at == 5


def test_message_from_payload() -> None:
    model = Message.from_payload({"id": "7", "message_type": "1"})
    assert model.id == 7
    assert model.message_type == 1
