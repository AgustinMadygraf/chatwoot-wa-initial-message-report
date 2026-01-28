"""List inboxes for a Chatwoot account."""

from __future__ import annotations

import sys
from typing import Any, Dict, List

import requests

from src_old.shared.config import get_env, load_env_file
from src_old.shared.logger import get_logger


def main() -> int:
    load_env_file()
    logger = get_logger("list_inboxes")

    base = get_env("CHATWOOT_BASE_URL")
    account = get_env("CHATWOOT_ACCOUNT_ID")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")

    if not base or not account or not token:
        logger.error("Missing CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID or CHATWOOT_API_ACCESS_TOKEN")
        return 2

    url = f"{base.rstrip('/')}/api/v1/accounts/{account}/inboxes"
    logger.info(f"GET {url}")

    try:
        resp = requests.get(url, headers={"api_access_token": token}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error(f"Request failed: {exc}")
        return 3

    data = resp.json()
    inboxes: List[Dict[str, Any]] = data.get("payload", []) if isinstance(data, dict) else []
    logger.info(f"Total inboxes: {len(inboxes)}")

    for inbox in inboxes:
        inbox_id = inbox.get("id")
        name = inbox.get("name")
        channel_type = inbox.get("channel_type")
        logger.info(f"- id={inbox_id} name={name} channel_type={channel_type}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
