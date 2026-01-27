"""List conversations for a given inbox (paged)."""

from __future__ import annotations

import sys
from typing import Any, Dict, List

import requests

from shared.config import get_env, load_env_file
from shared.logger import get_logger


def main() -> int:
    load_env_file()
    logger = get_logger("list_conversations")

    base = get_env("CHATWOOT_BASE_URL")
    account = get_env("CHATWOOT_ACCOUNT_ID")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")
    inbox_id = get_env("CHATWOOT_INBOX_ID")

    if not base or not account or not token or not inbox_id:
        logger.error(
            "Missing CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID, CHATWOOT_API_ACCESS_TOKEN or CHATWOOT_INBOX_ID"
        )
        return 2

    page = 1
    total = 0
    while True:
        url = f"{base.rstrip('/')}/api/v1/accounts/{account}/conversations"
        params = {"status": "all", "inbox_id": inbox_id, "page": page}
        logger.info(f"GET {url} params={params}")
        try:
            resp = requests.get(url, headers={"api_access_token": token}, params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error(f"Request failed: {exc}")
            return 3

        data = resp.json()
        payload: List[Dict[str, Any]] = data.get("payload", []) if isinstance(data, dict) else []
        logger.info(f"Page {page} items: {len(payload)}")
        if not payload:
            break

        for convo in payload[:5]:
            logger.info(
                f"- id={convo.get('id')} status={convo.get('status')} created_at={convo.get('created_at')}"
            )
        total += len(payload)
        page += 1

    logger.info(f"Total conversations listed: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
