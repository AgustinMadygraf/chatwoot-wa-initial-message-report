from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

from src_old.infrastructure.chatwoot_api.client import ChatwootClient
from src_old.entities.transform import categorize, normalize_literal
from src_old.shared.logger import Logger, get_logger


@dataclass
class InitialMessage:
    conversation_id: int
    inbox_id: int
    conversation_created_at: str
    message_id: int
    message_created_at: str
    initial_message_raw: str
    initial_message_literal: str
    category: str


def _parse_epoch(epoch: Optional[int]) -> Optional[datetime]:
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(epoch, tz=timezone.utc)
    except (TypeError, ValueError):
        return None


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.isoformat()


def _get_payload_list(payload: Dict) -> List[Dict]:
    if isinstance(payload.get("payload"), list):
        return payload["payload"]
    if isinstance(payload.get("data"), list):
        return payload["data"]
    if isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("payload"), list):
        return payload["data"]["payload"]
    return []

def _get_conversation_payload(conversation: Dict) -> Dict:
    if isinstance(conversation.get("payload"), dict):
        return conversation["payload"]
    if isinstance(conversation.get("data"), dict) and isinstance(conversation["data"].get("payload"), dict):
        return conversation["data"]["payload"]
    if isinstance(conversation.get("data"), dict):
        return conversation["data"]
    return conversation


def _get_messages(conversation: Dict) -> Optional[List[Dict]]:
    payload = _get_conversation_payload(conversation)
    if isinstance(payload.get("messages"), list):
        return payload["messages"]
    if isinstance(conversation.get("messages"), list):
        return conversation["messages"]
    return None


def list_conversations(
    client: ChatwootClient,
    inbox_id: str,
    since: Optional[datetime] = None,
    status: str = "all",
    per_page: Optional[int] = None,
    agent_id: Optional[int] = None,
    logger: Optional[Logger] = None,
) -> Iterable[Dict]:
    page = 1
    while True:
        if logger:
            logger.info(f"Consultando pagina {page} de conversaciones...")
        data = client.list_conversations(
            inbox_id,
            page,
            status=status,
            per_page=per_page,
            agent_id=agent_id,
        )
        items = _get_payload_list(data)
        if logger:
            logger.debug(f"Page {page} items: {len(items)}")
        if not items:
            if logger:
                logger.info("No hay mas conversaciones en la API.")
            break
        for item in items:
            if since is not None:
                created_at = _parse_epoch(item.get("created_at"))
                if created_at is None or created_at < since:
                    continue
            yield item
        page += 1


def _extract_initial_message(conversation: Dict) -> Optional[Tuple[Dict, Dict]]:
    messages = _get_messages(conversation)
    if not isinstance(messages, list):
        return None

    candidates = []
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
        created_at = _parse_epoch(msg.get("created_at"))
        candidates.append((created_at, msg))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0] is None, x[0]))
    return candidates[0][1], conversation


def extract_initial_messages(
    client: ChatwootClient,
    inbox_id: str,
    since: Optional[datetime] = None,
    status: str = "all",
    fallback_statuses: Optional[List[str]] = None,
    per_page: Optional[int] = None,
    agent_id: Optional[int] = None,
    logger: Optional[Logger] = None,
) -> Tuple[List[InitialMessage], Dict[str, int]]:
    results: List[InitialMessage] = []
    stats = {
        "total_listed": 0,
        "total_processed": 0,
        "total_excluded": 0,
    }

    logger = logger or get_logger("extractor")
    logger.info("Listando conversaciones...")

    def _iter_convos(active_status: str) -> Iterable[Dict]:
        return list_conversations(
            client,
            inbox_id,
            since=since,
            status=active_status,
            per_page=per_page,
            agent_id=agent_id,
            logger=logger,
        )

    seen_ids = set()
    active_statuses = [status]
    if status == "all" and fallback_statuses:
        active_statuses = [status] + fallback_statuses

    for active_status in active_statuses:
        if logger and active_status != status:
            logger.warning(f"Fallback status: {active_status}")
        for convo in _iter_convos(active_status):
            convo_id = convo.get("id")
            if stats["total_listed"] > 0 and stats["total_listed"] % 50 == 0:
                logger.info(
                    f"Progreso: {stats['total_listed']} listadas, "
                    f"{stats['total_processed']} procesadas, "
                    f"{stats['total_excluded']} excluidas"
                )
            if convo_id in seen_ids:
                continue
            seen_ids.add(convo_id)
            stats["total_listed"] += 1
            if convo_id is None:
                stats["total_excluded"] += 1
                continue
            logger.info(f"Buscando mensajes de conversacion {convo_id}...")
            detail = client.get_conversation(str(convo_id))
            extraction = _extract_initial_message(detail)
            if extraction is None:
                stats["total_excluded"] += 1
                continue
            msg, convo_detail = extraction
            convo_payload = _get_conversation_payload(convo_detail)
            convo_created_at = _to_iso(_parse_epoch(convo_payload.get("created_at")))
            msg_created_at = _to_iso(_parse_epoch(msg.get("created_at")))
            raw_text = msg.get("content", "")
            literal = normalize_literal(raw_text)
            category = categorize(raw_text)
            results.append(
                InitialMessage(
                    conversation_id=int(convo_id),
                    inbox_id=int(convo_payload.get("inbox_id") or inbox_id),
                    conversation_created_at=convo_created_at or "",
                    message_id=int(msg.get("id")),
                    message_created_at=msg_created_at or "",
                    initial_message_raw=raw_text,
                    initial_message_literal=literal,
                    category=category,
                )
            )
            stats["total_processed"] += 1

    logger.info(
        f"Listadas: {stats['total_listed']}, procesadas: {stats['total_processed']}, excluidas: {stats['total_excluded']}"
    )
    return results, stats
