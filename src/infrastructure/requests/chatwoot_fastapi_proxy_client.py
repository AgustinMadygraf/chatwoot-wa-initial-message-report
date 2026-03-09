"""
Path: src/infrastructure/requests/chatwoot_fastapi_proxy_client.py
"""

import logging
from typing import Any

import requests

from src.infrastructure.settings.env_settings import ChatwootSettings
from src.infrastructure.requests.chatwoot_inbox_mapper import map_to_inbox
from src.infrastructure.requests.inboxes_payload_mapper import normalize_inboxes_payload
from src.infrastructure.requests.sensitive_data_sanitizer import sanitize_payload
from src.use_case.chatwoot_contacts_query import (
    fetch_all_contacts_paginated,
    find_contact_in_paginated_contacts,
)
from src.use_case.errors import ProxyGatewayError

PAGE_SIZE = 15
logger = logging.getLogger(__name__)
class ChatwootProxyError(ProxyGatewayError):
    pass


class ChatwootFastApiProxyClient:
    def __init__(self, settings: ChatwootSettings) -> None:
        self._settings = settings

    def enforce_account_id(self, account_id: int) -> None:
        if account_id != self._settings.account_id:
            raise ChatwootProxyError(
                status_code=403,
                detail=(
                    "account_id no permitido en esta interfaz. "
                    "Usa el CHATWOOT_ACCOUNT_ID configurado en .env."
                ),
            )

    def get_inboxes(self, account_id: int) -> Any:
        response = self._forward_get(account_id=account_id, resource="inboxes")
        payload = self._parse_json(response)
        inboxes = normalize_inboxes_payload(payload)
        if inboxes is None:
            logger.error(
                "inboxes_invalid_payload payload_type=%s",
                type(payload).__name__,
            )
            raise ChatwootProxyError(
                status_code=502,
                detail="Formato inesperado de Chatwoot para listado de inboxes",
            )
        sanitized_inboxes = [sanitize_payload(inbox) for inbox in inboxes]
        mapped_inboxes = [map_to_inbox(inbox) for inbox in sanitized_inboxes]
        return [inbox.raw for inbox in mapped_inboxes]

    def get_inbox_by_id(self, account_id: int, inbox_id: int) -> dict[str, Any]:
        logger.info(
            "inbox_lookup_started account_id=%s inbox_id=%s",
            account_id,
            inbox_id,
        )
        payload = self.get_inboxes(account_id)
        inboxes = [map_to_inbox(inbox) for inbox in payload if isinstance(inbox, dict)]

        available_ids: list[int] = []
        for inbox in inboxes:
            current_id = inbox.id
            if current_id >= 0:
                available_ids.append(current_id)
            if current_id == inbox_id:
                logger.info(
                    "inbox_lookup_found account_id=%s inbox_id=%s total_inboxes=%s",
                    account_id,
                    inbox_id,
                    len(inboxes),
                )
                return {"payload": inbox.raw}

        logger.warning(
            "inbox_lookup_not_found account_id=%s inbox_id=%s total_inboxes=%s available_inbox_ids=%s",
            account_id,
            inbox_id,
            len(inboxes),
            available_ids,
        )
        raise ChatwootProxyError(status_code=404, detail="Inbox not found")

    def get_contacts(self, account_id: int, page: str | None) -> dict[str, Any]:
        if page is None:
            page = "1"

        if page.lower() == "all":
            return self._get_contacts_all(account_id)

        try:
            numeric_page = int(page)
            if numeric_page < 1:
                raise ValueError("page debe ser >= 1")
        except ValueError as exc:
            raise ChatwootProxyError(
                status_code=422,
                detail="Invalid page value. Use a number >= 1 or 'all'.",
            ) from exc

        response = self._forward_get(
            account_id=account_id,
            resource="contacts",
            params={"page": numeric_page},
        )
        payload = self._parse_json(response)
        if isinstance(payload, dict):
            return payload
        return {
            "payload": payload if isinstance(payload, list) else [],
            "meta": {
                "count": len(payload) if isinstance(payload, list) else 0,
                "current_page": numeric_page,
                "account_id": account_id,
            },
        }

    def get_contact_by_id(self, account_id: int, contact_id: int) -> dict[str, Any]:
        try:
            found = find_contact_in_paginated_contacts(
                fetch_page=lambda page_number: self._get_contacts_page(
                    account_id=account_id, page_number=page_number
                ),
                contact_id=contact_id,
                page_size=PAGE_SIZE,
            )
        except ValueError as exc:
            raise ChatwootProxyError(status_code=502, detail=str(exc)) from exc
        if found is None:
            raise ChatwootProxyError(status_code=404, detail="Contact not found")
        return {"payload": found.raw}

    def _get_contacts_all(self, account_id: int) -> dict[str, Any]:
        try:
            contacts = fetch_all_contacts_paginated(
                fetch_page=lambda page_number: self._get_contacts_page(
                    account_id=account_id, page_number=page_number
                ),
                page_size=PAGE_SIZE,
            )
        except ValueError as exc:
            raise ChatwootProxyError(status_code=502, detail=str(exc)) from exc

        return {
            "payload": contacts,
            "meta": {
                "count": len(contacts),
                "current_page": "all",
                "account_id": account_id,
            },
        }

    def _get_contacts_page(self, account_id: int, page_number: int) -> dict[str, Any]:
        response = self._forward_get(
            account_id=account_id,
            resource="contacts",
            params={"page": page_number},
        )
        payload = self._parse_json(response)
        if not isinstance(payload, dict):
            raise ChatwootProxyError(
                status_code=502,
                detail="Formato inesperado de Chatwoot para listado de contactos",
            )
        return payload

    def _forward_get(
        self,
        account_id: int,
        resource: str,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        url = f"{self._settings.base_url}/api/v1/accounts/{account_id}/{resource}"
        headers = {"api_access_token": self._settings.api_access_token}

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self._settings.timeout_seconds,
                verify=self._settings.tls_verify,
            )
        except requests.exceptions.Timeout as exc:
            raise ChatwootProxyError(
                status_code=504,
                detail=f"Timeout consultando Chatwoot: {exc}",
            ) from exc
        except requests.exceptions.SSLError as exc:
            raise ChatwootProxyError(
                status_code=502,
                detail=f"Error TLS/SSL con Chatwoot: {exc}",
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ChatwootProxyError(
                status_code=502,
                detail=f"Error de red consultando Chatwoot: {exc}",
            ) from exc

        if response.status_code >= 400:
            raise ChatwootProxyError(
                status_code=response.status_code,
                detail=response.text[:300],
            )
        return response

    @staticmethod
    def _parse_json(response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise ChatwootProxyError(
                status_code=502,
                detail=(
                    "Chatwoot devolvio una respuesta no-JSON. "
                    f"status={response.status_code}, body_parcial={response.text[:180]}"
                ),
            ) from exc
