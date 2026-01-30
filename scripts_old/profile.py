"""Fetch profile info to discover accessible accounts."""

from __future__ import annotations

import sys
from typing import Any

import requests

from src_old.shared.config import get_env, load_env_file
from src_old.shared.logger import get_logger


def main() -> int:
    load_env_file()
    logger = get_logger("profile")

    base = get_env("CHATWOOT_BASE_URL")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")

    if not base or not token:
        logger.error("Missing CHATWOOT_BASE_URL or CHATWOOT_API_ACCESS_TOKEN")
        return 2

    url = f"{base.rstrip('/')}/api/v1/profile"
    logger.info(f"GET {url}")

    try:
        resp = requests.get(url, headers={"api_access_token": token}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error(f"Request failed: {exc}")
        return 3

    data: dict[str, Any] = (
        resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else {}
    )
    logger.info("Profile response keys: " + ", ".join(sorted(data.keys())))
    if "access_token" in data:
        data["access_token"] = "***redacted***"
    if "pubsub_token" in data:
        data["pubsub_token"] = "***redacted***"

    accounts = data.get("accounts") or data.get("payload", {}).get("accounts")
    if isinstance(accounts, list):
        logger.info(f"Accounts in profile: {len(accounts)}")
        for acc in accounts:
            logger.info(f"- id={acc.get('id')} name={acc.get('name')}")
    else:
        logger.warning("No accounts field found in profile response")
        logger.warning(str(data)[:500])

    return 0


if __name__ == "__main__":
    sys.exit(main())
