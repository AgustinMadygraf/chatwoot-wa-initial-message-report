from dataclasses import dataclass
import os
from typing import Union

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


CA_BUNDLE_PATH = "certs/chatwoot-ca-bundle.pem"


@dataclass(frozen=True)
class ChatwootSettings:
    base_url: str
    account_id: int
    api_access_token: str
    timeout_seconds: float = 8.0
    tls_verify: Union[bool, str] = True


def load_chatwoot_settings() -> ChatwootSettings:
    if load_dotenv is not None:
        load_dotenv()

    base_url = _require_env("CHATWOOT_BASE_URL").rstrip("/")
    account_id_raw = _require_env("CHATWOOT_ACCOUNT_ID")
    api_access_token = _require_env("CHATWOOT_API_ACCESS_TOKEN")
    timeout_seconds = 8.0
    tls_verify = _load_tls_verify()

    try:
        account_id = int(account_id_raw)
    except ValueError as exc:
        raise ValueError("CHATWOOT_ACCOUNT_ID debe ser un entero") from exc

    return ChatwootSettings(
        base_url=base_url,
        account_id=account_id,
        api_access_token=api_access_token,
        timeout_seconds=timeout_seconds,
        tls_verify=tls_verify,
    )


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Falta variable de entorno requerida: {name}")
    return value


def _load_tls_verify() -> Union[bool, str]:
    if not os.path.exists(CA_BUNDLE_PATH):
        raise ValueError(
            f"Falta CA bundle TLS requerido en ruta hardcodeada: {CA_BUNDLE_PATH}"
        )
    return CA_BUNDLE_PATH
