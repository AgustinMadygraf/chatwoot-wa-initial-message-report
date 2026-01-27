"""Assign a user to an inbox via API."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

import requests

from shared.config import get_env, load_env_file
from shared.logger import get_logger


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assign a user to a Chatwoot inbox")
    parser.add_argument("--user-id", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    load_env_file()
    logger = get_logger("assign_inbox_member")
    args = _get_args()

    base = get_env("CHATWOOT_BASE_URL")
    account = get_env("CHATWOOT_ACCOUNT_ID")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")
    inbox_id = get_env("CHATWOOT_INBOX_ID")
    user_id = args.user_id or get_env("CHATWOOT_USER_ID")

    if not base or not account or not token or not inbox_id or not user_id:
        logger.error(
            "Missing CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID, CHATWOOT_API_ACCESS_TOKEN, CHATWOOT_INBOX_ID or user id"
        )
        return 2

    url = f"{base.rstrip('/')}/api/v1/accounts/{account}/inbox_members"
    payload = {"inbox_id": int(inbox_id), "user_ids": [int(user_id)]}
    logger.info(f"POST {url} payload={payload}")

    try:
        resp = requests.post(url, headers={"api_access_token": token}, json=payload, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error(f"Request failed: {exc}")
        return 3

    logger.info(f"Status: {resp.status_code}")
    logger.info("User assigned to inbox")
    return 0


if __name__ == "__main__":
    sys.exit(main())
