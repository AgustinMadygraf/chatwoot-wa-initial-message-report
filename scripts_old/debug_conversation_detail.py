"""Inspect a conversation detail response to understand message structure."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List

import requests

from src_old.shared.config import get_env, load_env_file
from src_old.shared.logger import get_logger


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect conversation detail")
    parser.add_argument("conversation_id", type=int)
    return parser.parse_args()


def _safe_keys(obj: Any) -> List[str]:
    return sorted(obj.keys()) if isinstance(obj, dict) else []


def main() -> int:
    load_env_file()
    logger = get_logger("debug_conversation_detail")
    args = _get_args()

    base = get_env("CHATWOOT_BASE_URL")
    account = get_env("CHATWOOT_ACCOUNT_ID")
    token = get_env("CHATWOOT_API_ACCESS_TOKEN")

    if not base or not account or not token:
        logger.error("Missing CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID or CHATWOOT_API_ACCESS_TOKEN")
        return 2

    url = f"{base.rstrip('/')}/api/v1/accounts/{account}/conversations/{args.conversation_id}"
    logger.info(f"GET {url}")

    try:
        resp = requests.get(url, headers={"api_access_token": token}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error(f"Request failed: {exc}")
        return 3

    data: Dict[str, Any] = resp.json()
    logger.info("Top-level keys: " + ", ".join(_safe_keys(data)))

    payload = data.get("payload")
    if isinstance(payload, dict):
        logger.info("payload keys: " + ", ".join(_safe_keys(payload)))
    elif isinstance(data.get("data"), dict):
        logger.info("data keys: " + ", ".join(_safe_keys(data["data"])))
        if isinstance(data["data"].get("payload"), dict):
            payload = data["data"]["payload"]
            logger.info("data.payload keys: " + ", ".join(_safe_keys(payload)))

    messages = None
    for container in (data, payload):
        if isinstance(container, dict) and isinstance(container.get("messages"), list):
            messages = container.get("messages")
            break

    if not isinstance(messages, list):
        logger.warning("No messages list found")
        return 0

    logger.info(f"messages count: {len(messages)}")
    if messages:
        sample = messages[0]
        logger.info("message keys: " + ", ".join(_safe_keys(sample)))
        logger.info(
            f"sample fields: id={sample.get('id')} sender_type={sample.get('sender_type')} content_type={sample.get('content_type')} private={sample.get('private')}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
