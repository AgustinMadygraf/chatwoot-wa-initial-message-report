from __future__ import annotations

from collections.abc import Callable, Iterable

from requests import RequestException

from application.ports.chatwoot_client import ChatwootClientPort
from application.ports.repositories import ConversationsRepositoryPort
from domain.chatwoot import Conversation
from shared.logger import Logger, get_logger


def _extract_conversations(payload: dict) -> Iterable[dict]:
    data = payload.get("payload")
    if isinstance(data, list):
        return data
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        nested = data.get("payload")
        if isinstance(nested, list):
            return nested
    return []

def _pick_address_for_debug(payload: dict) -> str | None:
    for key in ("phone_number", "email"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    meta = payload.get("meta")
    if isinstance(meta, dict):
        sender = meta.get("sender")
        if isinstance(sender, dict):
            for key in ("phone_number", "email"):
                value = sender.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            name = sender.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
    sender = payload.get("sender")
    if isinstance(sender, dict):
        for key in ("phone_number", "email"):
            value = sender.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        name = sender.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    meta_sender_name = payload.get("meta__sender__name")
    if isinstance(meta_sender_name, str) and meta_sender_name.strip():
        return meta_sender_name.strip()
    return None


def sync_conversations(
    client: ChatwootClientPort,
    repo: ConversationsRepositoryPort,
    logger: Logger | None = None,
    per_page: int | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> list[int]:
    logger = logger or get_logger("conversations")
    repo.ensure_table()

    page = 1
    conversation_ids: list[int] = []
    while True:
        logger.info(f"Consultando conversaciones (pagina {page})...")
        try:
            payload = client.list_conversations(page=page, per_page=per_page)
        except RequestException as exc:
            logger.warning(f"Conversaciones fallo en pagina {page}: {exc}")
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Conversaciones fallo inesperado en pagina {page}: {exc}")
            break
        items = list(_extract_conversations(payload))
        logger.debug(
            "Conversaciones recibidas",
            page=page,
            total=len(items),
        )
        if not items:
            logger.info("No hay mas conversaciones en la API.")
            break
        for convo in items:
            model = Conversation.from_payload(convo)
            if model.id is None:
                continue
            logger.debug(
                "Conversacion payload",
                conversation_id=model.id,
                inbox_id=convo.get("inbox_id"),
                account_id=convo.get("account_id"),
                status=convo.get("status"),
                sender=convo.get("meta", {}).get("sender") if isinstance(convo, dict) else None,
                address=_pick_address_for_debug(convo),
            )
            repo.upsert_conversation(convo)
            conversation_ids.append(int(model.id))
        if progress:
            progress(page, len(conversation_ids))
        page += 1

    logger.info(f"Conversaciones sincronizadas: {len(conversation_ids)}")
    return conversation_ids
