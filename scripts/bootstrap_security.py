from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.infrastructure.settings.bootstrap_security import (  # noqa: E402
    bootstrap_security_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Genera PROXY_API_KEY en .env y crea certs/chatwoot-ca-bundle.pem "
            "a partir del bundle de certifi."
        )
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=(
            "Base URL HTTPS de Chatwoot para intentar anexar su certificado "
            "al bundle generado."
        ),
    )
    parser.add_argument(
        "--force-ca",
        action="store_true",
        help="Reescribe certs/chatwoot-ca-bundle.pem desde certifi antes de anexar.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = bootstrap_security_artifacts(
            base_url=args.base_url,
            force_ca_overwrite=args.force_ca,
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1

    print("[OK] Setup de seguridad completado")
    print(f"ENV: {result.env_path} (creado: {'si' if result.env_created else 'no'})")
    print(f"PROXY_API_KEY: {result.proxy_api_key}")
    print(f"CA bundle: {result.ca_bundle_path}")
    print(f"Fuente base: {result.ca_bundle_source}")
    print(
        "Cert servidor anexado: "
        f"{'si' if result.appended_server_certificate else 'no'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
