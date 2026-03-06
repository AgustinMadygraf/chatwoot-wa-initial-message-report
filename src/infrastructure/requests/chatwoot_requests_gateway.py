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

    def fetch_contacts_page(self) -> ChatwootContactsResult:
        endpoint = self._build_endpoint("contacts")
        response, network_diag, error_detail = self._perform_get(endpoint)
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

    def fetch_contacts_raw_response(self) -> tuple[str, Response | None, str | None]:
        endpoint = self._build_endpoint("contacts")
        response, _, error_detail = self._perform_get(endpoint)
        return endpoint, response, error_detail

    def _build_endpoint(self, resource: str) -> str:
        return (
            f"{self._settings.base_url}/api/v1/accounts/"
            f"{self._settings.account_id}/{resource}"
        )

    def _perform_get(self, endpoint: str) -> tuple[Response | None, str, str | None]:
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
