"""
Path: src/use_case/chatwoot_contacts_query.py
"""

from typing import Any, Awaitable, Callable

from src.entities.chatwoot_contact import ChatwootContact


def find_contact_in_paginated_contacts(
    fetch_page: Callable[[int], dict[str, Any]],
    contact_id: int,
    page_size: int,
) -> ChatwootContact | None:
    first_payload = fetch_page(1)
    first_contacts = _extract_contacts(first_payload)
    found = _find_contact_raw_by_id(first_contacts, contact_id)
    if found is not None:
        return _to_contact(found)

    total_count = _extract_total_count(first_payload, default=len(first_contacts))
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    for page_number in range(2, total_pages + 1):
        payload = fetch_page(page_number)
        page_contacts = _extract_contacts(payload)
        found = _find_contact_raw_by_id(page_contacts, contact_id)
        if found is not None:
            return _to_contact(found)

    return None


async def find_contact_in_paginated_contacts_async(
    fetch_page: Callable[[int], Awaitable[dict[str, Any]]],
    contact_id: int,
    page_size: int,
) -> ChatwootContact | None:
    first_payload = await fetch_page(1)
    first_contacts = _extract_contacts(first_payload)
    found = _find_contact_raw_by_id(first_contacts, contact_id)
    if found is not None:
        return _to_contact(found)

    total_count = _extract_total_count(first_payload, default=len(first_contacts))
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    for page_number in range(2, total_pages + 1):
        payload = await fetch_page(page_number)
        page_contacts = _extract_contacts(payload)
        found = _find_contact_raw_by_id(page_contacts, contact_id)
        if found is not None:
            return _to_contact(found)

    return None


def fetch_all_contacts_paginated(
    fetch_page: Callable[[int], dict[str, Any]],
    page_size: int,
) -> list[Any]:
    first_payload = fetch_page(1)
    contacts = list(_extract_contacts(first_payload))
    total_count = _extract_total_count(first_payload, default=len(contacts))
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    for page_number in range(2, total_pages + 1):
        payload = fetch_page(page_number)
        contacts.extend(_extract_contacts(payload))

    return contacts


async def fetch_all_contacts_paginated_async(
    fetch_page: Callable[[int], Awaitable[dict[str, Any]]],
    page_size: int,
) -> list[Any]:
    first_payload = await fetch_page(1)
    contacts = list(_extract_contacts(first_payload))
    total_count = _extract_total_count(first_payload, default=len(contacts))
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    for page_number in range(2, total_pages + 1):
        payload = await fetch_page(page_number)
        contacts.extend(_extract_contacts(payload))

    return contacts


def _extract_contacts(payload: dict[str, Any]) -> list[Any]:
    raw_contacts = payload.get("payload", [])
    if isinstance(raw_contacts, list):
        return raw_contacts
    raise ValueError("Formato inesperado de Chatwoot para listado de contactos")


def _extract_total_count(payload: dict[str, Any], default: int) -> int:
    meta = payload.get("meta", {})
    if not isinstance(meta, dict):
        return default
    try:
        return int(meta.get("count", default))
    except (TypeError, ValueError):
        return default


def _find_contact_raw_by_id(contacts: list[Any], contact_id: int) -> dict[str, Any] | None:
    for contact in contacts:
        if not isinstance(contact, dict):
            continue
        try:
            current_id = int(contact.get("id"))
        except (TypeError, ValueError):
            continue
        if current_id == contact_id:
            return contact
    return None


def _to_contact(raw: dict[str, Any]) -> ChatwootContact:
    return ChatwootContact(id=int(raw.get("id", -1)), raw=raw)
