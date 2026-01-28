from typing import Dict, Iterable, Optional

from src_old.infrastructure.chatwoot_api.client import ChatwootClient
from src_old.infrastructure.mysql.contacts_repository import ContactsRepository
from src_old.shared.logger import Logger, get_logger


def _extract_contacts(payload: Dict) -> Iterable[Dict]:
    data = payload.get("payload")
    if isinstance(data, list):
        return data
    data = payload.get("data")
    if isinstance(data, list):
        return data
    return []


def sync_contacts(
    client: ChatwootClient,
    repo: ContactsRepository,
    logger: Optional[Logger] = None,
    per_page: Optional[int] = None,
) -> Dict[str, int]:
    logger = logger or get_logger("contacts")
    repo.ensure_table()

    page = 1
    stats = {"total_listed": 0, "total_upserted": 0, "total_skipped": 0}
    while True:
        logger.info(f"Consultando contactos (pagina {page})...")
        payload = client.list_contacts(page=page, per_page=per_page)
        items = list(_extract_contacts(payload))
        if not items:
            logger.info("No hay mas contactos en la API.")
            break
        for contact in items:
            contact_id = contact.get("id")
            if contact_id is None:
                stats["total_skipped"] += 1
                continue
            stats["total_listed"] += 1
            remote_updated_at = contact.get("updated_at")
            local_updated_at = repo.get_updated_at(int(contact_id))
            if local_updated_at is not None and remote_updated_at is not None:
                if int(remote_updated_at) <= int(local_updated_at):
                    stats["total_skipped"] += 1
                    continue
            repo.upsert_contact(contact)
            stats["total_upserted"] += 1

        page += 1

    logger.info(
        f"Contactos listados: {stats['total_listed']}, "
        f"upserted: {stats['total_upserted']}, skipped: {stats['total_skipped']}"
    )
    return stats
