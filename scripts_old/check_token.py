"""Check if Chatwoot API token can access the account."""

from __future__ import annotations

import sys
from typing import Optional

import requests

from src_old.shared.config import get_env, load_env_file
from src_old.shared.logger import get_logger


def main() -> int:
    load_env_file()
    logger = get_logger("check_token")

    base = get_env("CHATWOOT_BASE_URL")
    account = get_env("CHATWOOT_ACCOUNT_ID")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")

    if not base or not account or not token:
        logger.error("Missing CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID or CHATWOOT_API_ACCESS_TOKEN")
        return 2

    url = f"{base.rstrip('/')}/api/v1/accounts/{account}"
    logger.info(f"GET {url}")

    try:
        resp = requests.get(url, headers={"api_access_token": token}, timeout=15)
    except requests.RequestException as exc:
        logger.error(f"Request failed: {exc}")
        return 3

    logger.info(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        logger.info("Token OK: access granted to account")
        return 0
    if resp.status_code in (401, 403):
        logger.error("Token invalid or insufficient permissions")
        return 4

    logger.warning("Unexpected status; check response body")
    logger.warning(resp.text[:500])
    return 1


if __name__ == "__main__":
    sys.exit(main())
