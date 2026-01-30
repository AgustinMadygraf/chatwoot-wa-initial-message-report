from __future__ import annotations

import json
import os
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
    debug_inboxes = os.getenv("DEBUG_INBOXES", "").strip() == "1"
    if debug_inboxes:
        try:
            payload_dump = json.dumps(payload, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            payload_dump = str(payload)
        logger.debug(
            "Inboxes payload crudo recibido",
            payload=payload,
            payload_dump=payload_dump,
        )
        if getattr(logger, "fmt", "text") != "json":
            logger.debug(f"Inboxes payload crudo recibido: {payload_dump}")
    items = list(_extract_inboxes(payload))
    for inbox in items:
        if debug_inboxes:
            address_candidates = {
                "phone_number": inbox.get("phone_number"),
                "email": inbox.get("email"),
                "bot_name": inbox.get("bot_name"),
                "website_url": inbox.get("website_url"),
                "channel": inbox.get("channel"),
            }
            logger.debug(
                "Inbox campos de address",
                inbox_id=inbox.get("id"),
                channel_type=inbox.get("channel_type"),
                address_candidates=address_candidates,
            )
            if getattr(logger, "fmt", "text") != "json":
                logger.debug(
                    "Inbox campos de address: "
                    f"id={inbox.get('id')} channel_type={inbox.get('channel_type')} "
                    f"candidatos={address_candidates}"
                )
        model = Inbox.from_payload(inbox)
        repo.upsert_inbox(model.to_record())
    logger.info(f"Inboxes sincronizados: {len(items)}")
    return {"total_upserted": len(items)}
