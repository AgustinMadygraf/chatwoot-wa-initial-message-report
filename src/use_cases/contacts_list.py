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
