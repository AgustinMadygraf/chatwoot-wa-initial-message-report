import logging
from typing import Any

import requests

from src.infrastructure.settings.env_settings import ChatwootSettings

PAGE_SIZE = 15
logger = logging.getLogger(__name__)


class ChatwootProxyError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


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
        return self._normalize_inboxes_payload(payload)

    def get_inbox_by_id(self, account_id: int, inbox_id: int) -> dict[str, Any]:
        logger.info(
            "inbox_lookup_started account_id=%s inbox_id=%s",
            account_id,
            inbox_id,
        )
        payload = self.get_inboxes(account_id)

        available_ids: list[int] = []
        for inbox in payload:
            if not isinstance(inbox, dict):
                continue
            current_id = self._safe_int(inbox.get("id"), -1)
            if current_id >= 0:
                available_ids.append(current_id)
            if current_id == inbox_id:
                logger.info(
                    "inbox_lookup_found account_id=%s inbox_id=%s total_inboxes=%s",
                    account_id,
                    inbox_id,
                    len(payload),
                )
                return {"payload": inbox}

        logger.warning(
            "inbox_lookup_not_found account_id=%s inbox_id=%s total_inboxes=%s available_inbox_ids=%s",
            account_id,
            inbox_id,
            len(payload),
            available_ids,
        )
        raise ChatwootProxyError(status_code=404, detail="Inbox not found")

    def _normalize_inboxes_payload(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            nested = payload.get("payload")
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]

        logger.error(
            "inboxes_invalid_payload payload_type=%s",
            type(payload).__name__,
        )
        raise ChatwootProxyError(
            status_code=502,
            detail="Formato inesperado de Chatwoot para listado de inboxes",
        )

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
        first_payload = self._get_contacts_page(account_id=account_id, page_number=1)
        contacts = (
            first_payload.get("payload", [])
            if isinstance(first_payload.get("payload"), list)
            else []
        )

        found = self._find_contact_by_id(contacts, contact_id)
        if found is not None:
            return {"payload": found}

        meta = first_payload.get("meta", {}) if isinstance(first_payload.get("meta"), dict) else {}
        total_count = self._safe_int(meta.get("count"), len(contacts))
        total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)

        for page_number in range(2, total_pages + 1):
            payload = self._get_contacts_page(account_id=account_id, page_number=page_number)
            page_contacts = payload.get("payload", []) if isinstance(payload.get("payload"), list) else []
            found = self._find_contact_by_id(page_contacts, contact_id)
            if found is not None:
                return {"payload": found}

        raise ChatwootProxyError(status_code=404, detail="Contact not found")

    def _get_contacts_all(self, account_id: int) -> dict[str, Any]:
        first_payload = self._get_contacts_page(account_id=account_id, page_number=1)

        contacts = (
            list(first_payload.get("payload", []))
            if isinstance(first_payload.get("payload"), list)
            else []
        )
        meta = first_payload.get("meta", {}) if isinstance(first_payload.get("meta"), dict) else {}
        total_count = self._safe_int(meta.get("count"), len(contacts))
        total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)

        for page_number in range(2, total_pages + 1):
            payload = self._get_contacts_page(account_id=account_id, page_number=page_number)
            page_contacts = payload.get("payload", []) if isinstance(payload.get("payload"), list) else []
            contacts.extend(page_contacts)

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

    @staticmethod
    def _find_contact_by_id(contacts: list[Any], contact_id: int) -> dict[str, Any] | None:
        for contact in contacts:
            if not isinstance(contact, dict):
                continue
            if ChatwootFastApiProxyClient._safe_int(contact.get("id"), -1) == contact_id:
                return contact
        return None

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
