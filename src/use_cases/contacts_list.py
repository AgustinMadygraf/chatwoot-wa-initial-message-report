from __future__ import annotations

from typing import Dict, Iterable, Optional

from src.infrastructure.chatwoot_api.client import ChatwootClient
from src.shared.logger import Logger, get_logger


def _extract_contacts(payload: Dict) -> Iterable[Dict]:
    data = payload.get("payload")
    if isinstance(data, list):
        return data
    data = payload.get("data")
    if isinstance(data, list):
        return data
    return []


def list_all_contacts(
    client: ChatwootClient,
    logger: Optional[Logger] = None,
    per_page: Optional[int] = None,
) -> Iterable[Dict]:
    logger = logger or get_logger("contacts")
    page = 1
    while True:
        logger.info(f"Consultando contactos (pagina {page})...")
        payload = client.list_contacts(page=page, per_page=per_page)
        items = list(_extract_contacts(payload))
        if not items:
            logger.info("No hay mas contactos en la API.")
            break
        for contact in items:
            yield contact
        page += 1


def list_contacts_with_first_message(
    client: ChatwootClient,
    logger: Optional[Logger] = None,
    per_page: Optional[int] = None,
) -> Iterable[Dict]:
    logger = logger or get_logger("contacts")
    for contact in list_all_contacts(client, logger=logger, per_page=per_page):
        contact_id = contact.get("id")
        if contact_id is None:
            contact["first_message"] = ""
            yield contact
            continue
        try:
            convos_payload = client.list_contact_conversations(str(contact_id))
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Fallo listar conversaciones para contacto {contact_id}: {exc}")
            contact["first_message"] = ""
            yield contact
            continue
        contact["first_message"] = _extract_first_message_from_conversations(convos_payload) or ""
        yield contact


def _extract_first_message_from_conversations(payload: Dict) -> Optional[str]:
    conversations = payload.get("payload")
    if not isinstance(conversations, list):
        conversations = payload.get("data")
    if not isinstance(conversations, list):
        return None
    best_message = None
    best_created = None
    for convo in conversations:
        messages = _get_messages_from_conversation(convo)
        if not isinstance(messages, list):
            continue
        for msg in messages:
            if msg.get("private") is True:
                continue
            sender_type = str(msg.get("sender_type", "")).lower()
            if sender_type != "contact":
                continue
            if msg.get("content_type") != "text":
                continue
            content = msg.get("content")
            if not isinstance(content, str) or not content.strip():
                continue
            created_at = msg.get("created_at")
            if best_created is None or (
                created_at is not None and created_at < best_created
            ):
                best_created = created_at
                best_message = content
    return best_message


def _get_messages_from_conversation(conversation: Dict) -> Optional[Iterable[Dict]]:
    if isinstance(conversation.get("messages"), list):
        return conversation["messages"]
    payload = conversation.get("payload")
    if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
        return payload["messages"]
    data = conversation.get("data")
    if isinstance(data, dict) and isinstance(data.get("messages"), list):
        return data["messages"]
    return None
