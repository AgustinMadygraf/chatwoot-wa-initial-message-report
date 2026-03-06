import requests
from requests import Response

from src.entities.chatwoot_connection_result import ChatwootConnectionResult
from src.infrastructure.settings.env_settings import ChatwootSettings
from src.infrastructure.socket.network_checks import check_dns, check_tcp
from src.infrastructure.urllib.url_utils import extract_host_port


class ChatwootRequestsGateway:
    def __init__(self, settings: ChatwootSettings) -> None:
        self._settings = settings

    def validate_connection(self) -> ChatwootConnectionResult:
        endpoint = (
            f"{self._settings.base_url}/api/v1/accounts/"
            f"{self._settings.account_id}/inboxes"
        )
        host, port = extract_host_port(self._settings.base_url)

        if not host:
            return ChatwootConnectionResult(
                ok=False,
                status_code=None,
                endpoint=endpoint,
                detail="CHATWOOT_BASE_URL invalida: no se pudo obtener host.",
            )

        dns_ok, dns_detail = check_dns(host)
        if not dns_ok:
            return ChatwootConnectionResult(
                ok=False,
                status_code=None,
                endpoint=endpoint,
                detail=dns_detail,
            )

        tcp_ok, tcp_detail = check_tcp(host, port)
        if not tcp_ok:
            return ChatwootConnectionResult(
                ok=False,
                status_code=None,
                endpoint=endpoint,
                detail=tcp_detail,
            )
        network_diag = f"{dns_detail}; {tcp_detail}"

        headers = {"api_access_token": self._settings.api_access_token}

        try:
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=self._settings.timeout_seconds,
            )
        except requests.exceptions.Timeout:
            return ChatwootConnectionResult(
                ok=False,
                status_code=None,
                endpoint=endpoint,
                detail=(
                    "Timeout al conectar con Chatwoot. "
                    f"Revisa red, VPN/firewall y CHATWOOT_BASE_URL. ({network_diag})"
                ),
            )
        except requests.exceptions.ConnectionError as exc:
            return ChatwootConnectionResult(
                ok=False,
                status_code=None,
                endpoint=endpoint,
                detail=(
                    "No se pudo establecer conexion HTTP. "
                    f"Detalle tecnico: {exc}. ({network_diag})"
                ),
            )
        except requests.RequestException as exc:
            return ChatwootConnectionResult(
                ok=False,
                status_code=None,
                endpoint=endpoint,
                detail=f"Error HTTP inesperado: {exc}",
            )

        return self._map_response(
            endpoint=endpoint,
            response=response,
            network_diag=network_diag,
        )

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
