from __future__ import annotations

from collections.abc import Iterable

from application.ports.chatwoot_client import ChatwootClientPort
from application.ports.repositories import InboxesRepositoryPort
from domain.chatwoot import Inbox
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
    client: ChatwootClientPort,
    repo: InboxesRepositoryPort,
    logger: Logger | None = None,
) -> dict[str, int]:
    logger = logger or get_logger("inboxes")
    repo.ensure_table()
    payload = client.list_inboxes()
    items = list(_extract_inboxes(payload))
    for inbox in items:
        model = Inbox.from_payload(inbox)
        repo.upsert_inbox(model.to_record())
    logger.info(f"Inboxes sincronizados: {len(items)}")
    return {"total_upserted": len(items)}
