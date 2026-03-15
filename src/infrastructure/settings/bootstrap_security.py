from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import secrets
import shutil
import ssl
from urllib.parse import urlparse

import certifi

DEFAULT_CA_BUNDLE_PATH = Path("certs/chatwoot-ca-bundle.pem")
DEFAULT_ENV_FILE = Path(".env")
DEFAULT_ENV_TEMPLATE = Path(".env.example")


@dataclass(frozen=True)
class SecurityBootstrapResult:
    proxy_api_key: str
    env_path: Path
    env_created: bool
    ca_bundle_path: Path
    ca_bundle_source: Path
    appended_server_certificate: bool


def bootstrap_security_artifacts(
    base_url: str | None = None,
    env_path: Path = DEFAULT_ENV_FILE,
    env_template_path: Path = DEFAULT_ENV_TEMPLATE,
    ca_bundle_path: Path = DEFAULT_CA_BUNDLE_PATH,
    force_ca_overwrite: bool = False,
) -> SecurityBootstrapResult:
    env_created = _ensure_env_file(env_path=env_path, template_path=env_template_path)
    proxy_api_key = secrets.token_urlsafe(32)
    _upsert_env_key(env_path=env_path, key="PROXY_API_KEY", value=proxy_api_key)

    base_url_effective = (base_url or os.getenv("CHATWOOT_BASE_URL", "")).strip() or None
    ca_bundle_source, appended_server_certificate = _build_ca_bundle(
        ca_bundle_path=ca_bundle_path,
        base_url=base_url_effective,
        force_overwrite=force_ca_overwrite,
    )

    return SecurityBootstrapResult(
        proxy_api_key=proxy_api_key,
        env_path=env_path,
        env_created=env_created,
        ca_bundle_path=ca_bundle_path,
        ca_bundle_source=ca_bundle_source,
        appended_server_certificate=appended_server_certificate,
    )


def _ensure_env_file(env_path: Path, template_path: Path) -> bool:
    if env_path.exists():
        return False

    env_path.parent.mkdir(parents=True, exist_ok=True)
    if template_path.exists():
        shutil.copyfile(template_path, env_path)
    else:
        env_path.write_text("", encoding="utf-8")
    return True


def _upsert_env_key(env_path: Path, key: str, value: str) -> None:
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated = False
    next_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            next_lines.append(line)
            continue

        if stripped.startswith(f"{key}="):
            next_lines.append(f"{key}={value}")
            updated = True
            continue

        next_lines.append(line)

    if not updated:
        next_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")


def _build_ca_bundle(
    ca_bundle_path: Path,
    base_url: str | None,
    force_overwrite: bool,
) -> tuple[Path, bool]:
    ca_bundle_path.parent.mkdir(parents=True, exist_ok=True)
    certifi_bundle = Path(certifi.where())

    if force_overwrite or not ca_bundle_path.exists() or ca_bundle_path.stat().st_size == 0:
        shutil.copyfile(certifi_bundle, ca_bundle_path)

    appended_server_certificate = False
    if base_url is not None:
        server_cert_pem = _fetch_server_certificate_pem(base_url)
        existing = ca_bundle_path.read_text(encoding="utf-8")
        cert_block = server_cert_pem.strip()
        if cert_block not in existing:
            ca_bundle_path.write_text(
                existing.rstrip() + "\n\n" + cert_block + "\n",
                encoding="utf-8",
            )
            appended_server_certificate = True

    return certifi_bundle, appended_server_certificate


def _fetch_server_certificate_pem(base_url: str) -> str:
    parsed = urlparse(base_url if "://" in base_url else f"https://{base_url}")
    if parsed.scheme.lower() != "https":
        raise ValueError("CHATWOOT_BASE_URL debe usar esquema https://")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("No se pudo extraer hostname de CHATWOOT_BASE_URL")

    port = parsed.port or 443
    try:
        return ssl.get_server_certificate((hostname, port))
    except OSError as exc:
        raise ValueError(
            f"No se pudo descargar certificado TLS de {hostname}:{port}. "
            "Verifica conectividad y valor de CHATWOOT_BASE_URL."
        ) from exc
