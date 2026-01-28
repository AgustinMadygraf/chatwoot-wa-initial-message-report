"""Check Chatwoot health endpoint."""

from __future__ import annotations

import sys

import requests

from src_old.shared.config import get_env, load_env_file
from src_old.shared.logger import get_logger


def _fetch(url: str, token: str | None) -> requests.Response:
    headers = {"api_access_token": token} if token else {}
    return requests.get(url, headers=headers, timeout=10)


def main() -> int:
    load_env_file()
    logger = get_logger("check_health")

    base = get_env("CHATWOOT_BASE_URL")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")
    if not base:
        logger.error("Missing CHATWOOT_BASE_URL")
        return 2

    url = f"{base.rstrip('/')}/api/v1/health"
    logger.info(f"GET {url}")

    try:
        resp = _fetch(url, token=None)
    except requests.RequestException as exc:
        logger.error(f"Request failed: {exc}")
        return 3

    logger.info(f"Status: {resp.status_code}")
    if resp.status_code == 404 and token:
        fallback = f"{base.rstrip('/')}/api/v1/profile"
        logger.info(f"Health not available, trying {fallback}")
        try:
            resp = _fetch(fallback, token=token)
        except requests.RequestException as exc:
            logger.error(f"Request failed: {exc}")
            return 3
        logger.info(f"Profile status: {resp.status_code}")

    if resp.headers.get("Content-Type", "").startswith("application/json"):
        logger.info("JSON response received (omitted for safety)")
    else:
        logger.info("Non-JSON response received (omitted for safety)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
