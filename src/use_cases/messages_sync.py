from __future__ import annotations

from collections.abc import Callable, Iterable

from requests import RequestException

from infrastructure.chatwoot_api.client import ChatwootClient
from infrastructure.pymysql.messages_repository import MessagesRepository
from shared.logger import Logger, get_logger


def _extract_messages(payload: dict) -> Iterable[dict]:
    data = payload.get("payload")
    if isinstance(data, list):
        return data
    data = payload.get("data")
    if isinstance(data, list):
        return data
    return []


def sync_messages(
    client: ChatwootClient,
    repo: MessagesRepository,
    conversation_ids: Iterable[int],
    logger: Logger | None = None,
    per_page: int | None = None,
    progress: Callable[[int, int, int], None] | None = None,
) -> dict[str, int]:
    logger = logger or get_logger("messages")
    repo.ensure_table()

    total = 0
    errors = 0
    for convo_id in conversation_ids:
        page = 1
        while True:
            try:
                payload = client.list_conversation_messages(
                    conversation_id=convo_id, page=page, per_page=per_page
                )
            except RequestException as exc:
                errors += 1
                logger.warning(f"Mensajes fallo en conversation {convo_id}, pagina {page}: {exc}")
                break
            except Exception as exc:  # noqa: BLE001
                errors += 1
                logger.warning(
                    f"Mensajes fallo inesperado en conversation {convo_id}, pagina {page}: {exc}"
                )
                break
            items = list(_extract_messages(payload))
            if not items:
                break
            for message in items:
                repo.upsert_message(message)
                total += 1
            if progress:
                progress(convo_id, total, errors)
            page += 1
        if progress:
            progress(convo_id, total, errors)

    logger.info(f"Mensajes sincronizados: {total}")
    return {"total_upserted": total, "total_errors": errors}
