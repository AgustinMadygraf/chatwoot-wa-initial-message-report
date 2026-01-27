"""List members assigned to a specific inbox."""

from __future__ import annotations

import sys
from typing import Any, Dict, List

import requests

from shared.config import get_env, load_env_file
from shared.logger import get_logger


def main() -> int:
    load_env_file()
    logger = get_logger("list_inbox_members")

    base = get_env("CHATWOOT_BASE_URL")
    account = get_env("CHATWOOT_ACCOUNT_ID")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")
    inbox_id = get_env("CHATWOOT_INBOX_ID")

    if not base or not account or not token or not inbox_id:
        logger.error(
            "Missing CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID, CHATWOOT_API_ACCESS_TOKEN or CHATWOOT_INBOX_ID"
        )
        return 2

    url = f"{base.rstrip('/')}/api/v1/accounts/{account}/inbox_members/{inbox_id}"
    logger.info(f"GET {url}")

    try:
        resp = requests.get(url, headers={"api_access_token": token}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error(f"Request failed: {exc}")
        return 3

    data: Dict[str, Any] = resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else {}
    members: List[Dict[str, Any]] = []
    if isinstance(data.get("payload"), list):
        members = data["payload"]

    logger.info(f"Members in inbox {inbox_id}: {len(members)}")
    for member in members:
        logger.info(f"- id={member.get('id')} name={member.get('name')} email={member.get('email')} role={member.get('role')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
