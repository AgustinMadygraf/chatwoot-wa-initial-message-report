"""Inspect the conversations endpoint response structure without dumping sensitive data."""

from __future__ import annotations

import sys
from typing import Any, Dict, Optional

import requests

from shared.config import get_env, load_env_file
from shared.logger import get_logger


def _maybe_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def main() -> int:
    load_env_file()
    logger = get_logger("debug_conversations")

    base = get_env("CHATWOOT_BASE_URL")
    account = get_env("CHATWOOT_ACCOUNT_ID")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")

    if not base or not account or not token:
        logger.error("Missing CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID or CHATWOOT_API_ACCESS_TOKEN")
        return 2

    inbox_id = get_env("CHATWOOT_INBOX_ID")
    status = get_env("CHATWOOT_STATUS") or "all"
    per_page = _maybe_int(get_env("CHATWOOT_PER_PAGE"))
    agent_id = _maybe_int(get_env("CHATWOOT_AGENT_ID"))
    page = _maybe_int(get_env("CHATWOOT_PAGE")) or 1

    params: Dict[str, Any] = {"status": status, "page": page}
    if inbox_id:
        params["inbox_id"] = inbox_id
    if per_page:
        params["per_page"] = per_page
    if agent_id:
        params["agent_id"] = agent_id

    url = f"{base.rstrip('/')}/api/v1/accounts/{account}/conversations"
    logger.info(f"GET {url} params={params}")

    try:
        resp = requests.get(url, headers={"api_access_token": token}, params=params, timeout=15)
    except requests.RequestException as exc:
        logger.error(f"Request failed: {exc}")
        return 3

    logger.info(f"Status: {resp.status_code}")
    content_type = resp.headers.get("Content-Type", "")
    logger.info(f"Content-Type: {content_type}")

    data: Dict[str, Any] = {}
    if content_type.startswith("application/json"):
        try:
            data = resp.json()
        except ValueError:
            logger.warning("JSON decode failed")
            return 4

    if not data:
        logger.warning("Empty JSON body")
        return 0

    logger.info("Top-level keys: " + ", ".join(sorted(data.keys())))

    payload = data.get("payload")
    if isinstance(payload, list):
        logger.info(f"payload is list, len={len(payload)}")
    elif isinstance(payload, dict):
        logger.info("payload is dict, keys: " + ", ".join(sorted(payload.keys())))
        for key in ("data", "conversations"):
            if isinstance(payload.get(key), list):
                logger.info(f"payload.{key} len={len(payload.get(key))}")
    else:
        logger.info("payload missing or not list/dict")

    for key in ("meta", "count", "data", "conversations"):
        if key in data:
            value = data.get(key)
            if isinstance(value, list):
                logger.info(f"{key} is list, len={len(value)}")
            elif isinstance(value, dict):
                logger.info(f"{key} is dict, keys: " + ", ".join(sorted(value.keys())))
            else:
                logger.info(f"{key}={value}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
