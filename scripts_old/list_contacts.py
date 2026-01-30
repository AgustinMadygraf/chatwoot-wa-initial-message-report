"""List contacts for an account (paged)."""

from __future__ import annotations

import sys
from typing import Any

import requests

from src_old.shared.config import get_env, load_env_file
from src_old.shared.logger import get_logger


def main() -> int:
    load_env_file()
    logger = get_logger("list_contacts")

    base = get_env("CHATWOOT_BASE_URL")
    account = get_env("CHATWOOT_ACCOUNT_ID")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")

    if not base or not account or not token:
        logger.error("Missing CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID or CHATWOOT_API_ACCESS_TOKEN")
        return 2

    page = 1
    total = 0
    while True:
        url = f"{base.rstrip('/')}/api/v1/accounts/{account}/contacts"
        params = {"page": page}
        logger.info(f"GET {url} params={params}")
        try:
            resp = requests.get(url, headers={"api_access_token": token}, params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error(f"Request failed: {exc}")
            return 3

        data = resp.json()
        payload: list[dict[str, Any]] = data.get("payload", []) if isinstance(data, dict) else []
        logger.info(f"Page {page} items: {len(payload)}")
        if not payload:
            break

        for contact in payload[:10]:
            logger.info(
                f"- id={contact.get('id')} name={contact.get('name')} phone={contact.get('phone_number')}"
            )
        total += len(payload)
        page += 1

    logger.info(f"Total contacts listed: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
