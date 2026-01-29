from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Optional

from src.infrastructure.chatwoot_api.client import ChatwootClient
from src.infrastructure.pymysql.conversations_repository import ConversationsRepository
from src.shared.logger import Logger, get_logger
from requests import RequestException


def _extract_conversations(payload: Dict) -> Iterable[Dict]:
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


def sync_conversations(
    client: ChatwootClient,
    repo: ConversationsRepository,
    logger: Optional[Logger] = None,
    per_page: Optional[int] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> List[int]:
    logger = logger or get_logger("conversations")
    repo.ensure_table()

    page = 1
    conversation_ids: List[int] = []
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
        if not items:
            logger.info("No hay mas conversaciones en la API.")
            break
        for convo in items:
            convo_id = convo.get("id")
            if convo_id is None:
                continue
            repo.upsert_conversation(convo)
            conversation_ids.append(int(convo_id))
        if progress:
            progress(page, len(conversation_ids))
        page += 1

    logger.info(f"Conversaciones sincronizadas: {len(conversation_ids)}")
    return conversation_ids
