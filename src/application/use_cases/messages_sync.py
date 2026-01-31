from __future__ import annotations

from collections.abc import Callable, Iterable
import inspect

from requests import RequestException

from application.ports.chatwoot_client import ChatwootClientPort
from application.ports.repositories import MessagesRepositoryPort
from domain.chatwoot import Message
from shared.logger import Logger, get_logger


def _extract_messages(payload: dict) -> Iterable[dict]:
    data = payload.get("payload")
    if isinstance(data, list):
        return data
    data = payload.get("data")
    if isinstance(data, list):
        return data
    return []


def _next_page(payload: dict, current_page: int) -> int | None:
    meta = payload.get("meta")
    if isinstance(meta, dict):
        next_page = meta.get("next_page")
        if isinstance(next_page, int):
            return next_page
        if next_page is None and "next_page" in meta:
            return None
    return current_page + 1


def sync_messages(
    client: ChatwootClientPort,
    repo: MessagesRepositoryPort,
    conversation_ids: Iterable[int],
    logger: Logger | None = None,
    per_page: int | None = None,
    progress: Callable[[int, int, int], None] | None = None,
) -> dict[str, int]:
    logger = logger or get_logger("messages")
    repo.ensure_table()
    supports_before = _supports_param(client.list_conversation_messages, "before")

    total = 0
    errors = 0
    for convo_id in conversation_ids:
        logger.debug("Mensajes: inicio conversacion", conversation_id=convo_id)
        page = 1
        before: int | None = None
        last_page_ids: tuple[int | None, int | None] | None = None
        while True:
            logger.debug(
                "Mensajes: consultando pagina",
                conversation_id=convo_id,
                page=page,
                before=before,
                per_page=per_page,
            )
            try:
                if supports_before:
                    payload = client.list_conversation_messages(
                        conversation_id=convo_id,
                        page=page if before is None else None,
                        per_page=per_page,
                        before=before,
                    )
                else:
                    payload = client.list_conversation_messages(
                        conversation_id=convo_id,
                        page=page,
                        per_page=per_page,
                    )
            except RequestException as exc:
                errors += 1
                logger.warning(f"Mensajes fallo en conversation {convo_id}, pagina {page}: {exc}")
                break
            except (ValueError, KeyError, TypeError) as exc:
                errors += 1
                logger.warning(
                    f"Mensajes fallo inesperado en conversation {convo_id}, pagina {page}: {exc}"
                )
                break
            logger.debug(
                "Mensajes: payload meta",
                conversation_id=convo_id,
                page=page,
                meta=payload.get("meta"),
                payload_keys=list(payload.keys()),
            )
            items = list(_extract_messages(payload))
            page_ids = (
                items[0].get("id") if items else None,
                items[-1].get("id") if items else None,
            )
            logger.debug(
                "Mensajes: pagina recibida",
                conversation_id=convo_id,
                page=page,
                count=len(items),
                first_id=page_ids[0],
                last_id=page_ids[1],
                sample_sender_type=items[0].get("sender_type") if items else None,
                sample_message_type=items[0].get("message_type") if items else None,
            )
            if not items:
                logger.debug(
                    "Mensajes: sin items, fin conversacion",
                    conversation_id=convo_id,
                    page=page,
                )
                break
            if last_page_ids == page_ids:
                logger.warning(
                    "Mensajes: pagina repetida, deteniendo paginacion",
                    conversation_id=convo_id,
                    page=page,
                    first_id=page_ids[0],
                    last_id=page_ids[1],
                )
                if supports_before and before is None and page_ids[0] is not None:
                    logger.warning(
                        "Mensajes: intentando paginacion por cursor (before)",
                        conversation_id=convo_id,
                        before=page_ids[0],
                    )
                    before = int(page_ids[0])
                    last_page_ids = None
                    continue
                break
            last_page_ids = page_ids
            for message in items:
                model = Message.from_payload(message)
                if model.message_type not in (0, 1):
                    logger.debug(
                        "Mensajes: omitido por message_type",
                        conversation_id=convo_id,
                        message_id=model.id,
                        message_type=model.message_type,
                    )
                    continue
                repo.upsert_message(model.to_record())
                total += 1
            logger.debug(
                "Mensajes: pagina upserted",
                conversation_id=convo_id,
                page=page,
                total=total,
                errors=errors,
            )
            if progress:
                progress(convo_id, total, errors)
            if supports_before and before is not None:
                before = int(page_ids[0]) if page_ids[0] is not None else None
                if before is None:
                    break
            else:
                next_page = _next_page(payload, page)
                if next_page is None:
                    break
                page = next_page
        if progress:
            progress(convo_id, total, errors)
        logger.debug(
            "Mensajes: fin conversacion",
            conversation_id=convo_id,
            total=total,
            errors=errors,
        )

    logger.info(f"Mensajes sincronizados: {total}")
    return {"total_upserted": total, "total_errors": errors}


def _supports_param(func: Callable[..., object], name: str) -> bool:
    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):
        return False
    if name in params:
        return True
    return any(param.kind == param.VAR_KEYWORD for param in params.values())
