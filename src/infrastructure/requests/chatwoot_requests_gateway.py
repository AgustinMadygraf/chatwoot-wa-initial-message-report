import math
import time
from collections.abc import Callable

import requests
from requests import Response

from src.entities.chatwoot_connection_result import ChatwootConnectionResult
from src.entities.chatwoot_contacts_result import ChatwootContactsResult, ContactRow
from src.infrastructure.settings.env_settings import ChatwootSettings
from src.infrastructure.socket.network_checks import check_dns, check_tcp
from src.infrastructure.urllib.url_utils import extract_host_port


class ChatwootRequestsGateway:
    def __init__(self, settings: ChatwootSettings) -> None:
        self._settings = settings

    def validate_connection(self) -> ChatwootConnectionResult:
        endpoint = self._build_endpoint("inboxes")
        response, network_diag, error_detail = self._perform_get(endpoint)
        if error_detail is not None:
            return ChatwootConnectionResult(
                ok=False,
                status_code=None,
                endpoint=endpoint,
                detail=error_detail,
            )
        assert response is not None

        return self._map_response(
            endpoint=endpoint,
            response=response,
            network_diag=network_diag,
        )

    def fetch_contacts_page(self, page: int = 1) -> ChatwootContactsResult:
        endpoint = self._build_endpoint("contacts")
        response, network_diag, error_detail = self._perform_get(
            endpoint,
            params={"page": page},
        )
        if error_detail is not None:
            return ChatwootContactsResult(
                ok=False,
                status_code=None,
                endpoint=endpoint,
                detail=error_detail,
                contacts=[],
            )
        assert response is not None

        if 200 <= response.status_code <= 299:
            if response.status_code == 204:
                return ChatwootContactsResult(
                    ok=True,
                    status_code=response.status_code,
                    endpoint=endpoint,
                    detail=f"Respuesta sin contenido. ({network_diag})",
                    contacts=[],
                )

            contacts, parse_detail = self._extract_contacts(response)
            return ChatwootContactsResult(
                ok=True,
                status_code=response.status_code,
                endpoint=endpoint,
                detail=f"Pagina de contactos obtenida. {parse_detail} ({network_diag})",
                contacts=contacts,
            )

        if response.status_code in (401, 403):
            return ChatwootContactsResult(
                ok=False,
                status_code=response.status_code,
                endpoint=endpoint,
                detail=(
                    "Conectividad OK pero autenticacion/autorizacion invalida "
                    f"(token o permisos). ({network_diag})"
                ),
                contacts=[],
            )

        return ChatwootContactsResult(
            ok=False,
            status_code=response.status_code,
            endpoint=endpoint,
            detail=(
                "Chatwoot respondio con estado no esperado. "
                f"Body parcial: {response.text[:180]}. ({network_diag})"
            ),
            contacts=[],
        )

    def fetch_contacts_raw_response(
        self,
        page: int = 1,
    ) -> tuple[str, Response | None, str | None]:
        endpoint = self._build_endpoint("contacts")
        response, _, error_detail = self._perform_get(endpoint, params={"page": page})
        return endpoint, response, error_detail

    def fetch_contacts_raw_response_with_retries(
        self,
        page: int = 1,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        on_retry: Callable[[int], None] | None = None,
    ) -> tuple[str, Response | None, str | None]:
        endpoint = self._build_endpoint("contacts")
        last_error: str | None = None

        for attempt in range(1, max_retries + 1):
            current_endpoint, response, error_detail = self.fetch_contacts_raw_response(
                page=page
            )
            endpoint = current_endpoint
            if error_detail is None:
                return endpoint, response, None
            last_error = error_detail
            if attempt < max_retries:
                if on_retry is not None:
                    on_retry(attempt)
                time.sleep(retry_delay_seconds)

        return endpoint, None, last_error

    def fetch_all_contacts_raw(
        self,
        max_retries: int = 3,
        request_delay_seconds: float = 1.0,
        on_page_downloaded: Callable[[int, int], None] | None = None,
        on_retry: Callable[[int, int, int], None] | None = None,
    ) -> tuple[str, list[dict], Response | None, str | None]:
        endpoint, first_response, first_error = self.fetch_contacts_raw_response_with_retries(
            page=1,
            max_retries=max_retries,
            retry_delay_seconds=request_delay_seconds,
            on_retry=(
                (lambda attempt: on_retry(1, 1, attempt))
                if on_retry is not None
                else None
            ),
        )
        if first_error is not None:
            return endpoint, [], None, first_error
        assert first_response is not None

        if not 200 <= first_response.status_code <= 299:
            return (
                endpoint,
                [],
                first_response,
                (
                    f"Estado HTTP no valido: {first_response.status_code}. "
                    f"Body parcial: {first_response.text[:180]}"
                ),
            )

        first_payload = self._parse_json_payload(first_response)
        contacts_all = self._extract_raw_contacts(first_payload)
        total_count, current_page = self._extract_pagination_meta(first_payload)
        total_pages = max(1, math.ceil(total_count / 15))

        if on_page_downloaded is not None:
            on_page_downloaded(1, total_pages)

        for page in range(current_page + 1, total_pages + 1):
            time.sleep(request_delay_seconds)
            _, response, error_detail = self.fetch_contacts_raw_response_with_retries(
                page=page,
                max_retries=max_retries,
                retry_delay_seconds=request_delay_seconds,
                on_retry=(
                    (lambda attempt, current_page=page, total=total_pages: on_retry(current_page, total, attempt))
                    if on_retry is not None
                    else None
                ),
            )
            if error_detail is not None:
                return endpoint, contacts_all, None, error_detail
            assert response is not None
            if not 200 <= response.status_code <= 299:
                return (
                    endpoint,
                    contacts_all,
                    response,
                    (
                        f"Estado HTTP no valido en pagina {page}: {response.status_code}. "
                        f"Body parcial: {response.text[:180]}"
                    ),
                )

            payload = self._parse_json_payload(response)
            contacts_all.extend(self._extract_raw_contacts(payload))
            if on_page_downloaded is not None:
                on_page_downloaded(page, total_pages)

        return endpoint, contacts_all, first_response, None

    def _build_endpoint(self, resource: str) -> str:
        return (
            f"{self._settings.base_url}/api/v1/accounts/"
            f"{self._settings.account_id}/{resource}"
        )

    def _perform_get(
        self,
        endpoint: str,
        params: dict[str, int] | None = None,
    ) -> tuple[Response | None, str, str | None]:
        host, port = extract_host_port(self._settings.base_url)

        if not host:
            return None, "", "CHATWOOT_BASE_URL invalida: no se pudo obtener host."

        dns_ok, dns_detail = check_dns(host)
        if not dns_ok:
            return None, "", dns_detail

        tcp_ok, tcp_detail = check_tcp(host, port)
        if not tcp_ok:
            return None, "", tcp_detail
        network_diag = f"{dns_detail}; {tcp_detail}"

        headers = {"api_access_token": self._settings.api_access_token}

        try:
            response = requests.get(
                endpoint,
                headers=headers,
                params=params,
                timeout=self._settings.timeout_seconds,
                verify=self._settings.tls_verify,
            )
            return response, network_diag, None
        except requests.exceptions.SSLError as exc:
            return (
                None,
                network_diag,
                (
                    "Fallo la verificacion SSL/TLS del servidor. "
                    "Configura CHATWOOT_CA_BUNDLE con el certificado CA/intermedio "
                    "o usa CHATWOOT_TLS_VERIFY=false solo para pruebas. "
                    f"Detalle tecnico: {exc}. ({network_diag})"
                ),
            )
        except requests.exceptions.Timeout:
            return (
                None,
                network_diag,
                (
                    "Timeout al conectar con Chatwoot. "
                    f"Revisa red, VPN/firewall y CHATWOOT_BASE_URL. ({network_diag})"
                ),
            )
        except requests.exceptions.ConnectionError as exc:
            return (
                None,
                network_diag,
                (
                    "No se pudo establecer conexion HTTP. "
                    f"Detalle tecnico: {exc}. ({network_diag})"
                ),
            )
        except requests.RequestException as exc:
            return None, network_diag, f"Error HTTP inesperado: {exc}"

    @staticmethod
    def _extract_contacts(response: Response) -> tuple[list[ContactRow], str]:
        try:
            payload = response.json()
        except ValueError:
            return [], "No se pudo parsear JSON de respuesta."

        raw_contacts = []
        if isinstance(payload, list):
            raw_contacts = payload
        elif isinstance(payload, dict):
            if isinstance(payload.get("payload"), list):
                raw_contacts = payload.get("payload", [])
            elif isinstance(payload.get("data"), list):
                raw_contacts = payload.get("data", [])

        contacts: list[ContactRow] = []
        for item in raw_contacts:
            if not isinstance(item, dict):
                continue
            contacts.append(
                ContactRow(
                    id=item.get("id", ""),
                    name=str(item.get("name", "") or ""),
                    phone_number=str(item.get("phone_number", "") or ""),
                    email=str(item.get("email", "") or ""),
                    created_at=str(item.get("created_at", "") or ""),
                )
            )
        return contacts, f"Contactos parseados: {len(contacts)}."

    @staticmethod
    def _parse_json_payload(response: Response) -> object:
        return response.json()

    @staticmethod
    def _extract_raw_contacts(payload: object) -> list[dict]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            if isinstance(payload.get("payload"), list):
                return [item for item in payload["payload"] if isinstance(item, dict)]
            if isinstance(payload.get("data"), list):
                return [item for item in payload["data"] if isinstance(item, dict)]
        return []

    @staticmethod
    def _extract_pagination_meta(payload: object) -> tuple[int, int]:
        if not isinstance(payload, dict):
            return 0, 1
        meta = payload.get("meta", {})
        if not isinstance(meta, dict):
            return 0, 1
        try:
            count = int(meta.get("count", 0) or 0)
        except (TypeError, ValueError):
            count = 0
        try:
            current_page = int(meta.get("current_page", 1) or 1)
        except (TypeError, ValueError):
            current_page = 1
        return count, current_page

    @staticmethod
    def _map_response(
        endpoint: str,
        response: Response,
        network_diag: str,
    ) -> ChatwootConnectionResult:
        if response.status_code == 200:
            return ChatwootConnectionResult(
                ok=True,
                status_code=200,
                endpoint=endpoint,
                detail=(
                    "Conexion y autenticacion validadas contra Chatwoot. "
                    f"({network_diag})"
                ),
            )

        if response.status_code in (401, 403):
            return ChatwootConnectionResult(
                ok=False,
                status_code=response.status_code,
                endpoint=endpoint,
                detail=(
                    "Conectividad OK pero autenticacion/autorizacion invalida "
                    f"(token o permisos). ({network_diag})"
                ),
            )

        return ChatwootConnectionResult(
            ok=False,
            status_code=response.status_code,
            endpoint=endpoint,
            detail=(
                "Chatwoot respondio con estado no esperado. "
                f"Body parcial: {response.text[:180]}. ({network_diag})"
            ),
        )
