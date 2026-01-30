from __future__ import annotations

from collections.abc import Iterable

from infrastructure.chatwoot_api.client import ChatwootClient
from infrastructure.pymysql.inboxes_repository import InboxesRepository
from shared.logger import Logger, get_logger


def _extract_inboxes(payload: dict) -> Iterable[dict]:
    data = payload.get("payload")
    if isinstance(data, list):
        return data
    data = payload.get("data")
    if isinstance(data, list):
        return data
    return []


def sync_inboxes(
    client: ChatwootClient,
    repo: InboxesRepository,
    logger: Logger | None = None,
) -> dict[str, int]:
    logger = logger or get_logger("inboxes")
    repo.ensure_table()
    payload = client.list_inboxes()
    items = list(_extract_inboxes(payload))
    for inbox in items:
        repo.upsert_inbox(inbox)
    logger.info(f"Inboxes sincronizados: {len(items)}")
    return {"total_upserted": len(items)}
