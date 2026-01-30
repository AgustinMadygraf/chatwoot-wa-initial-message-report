from __future__ import annotations

import json
import os
import sys

from infrastructure.chatwoot_api.client import ChatwootClient, ChatwootClientConfig


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"Missing env var: {name}")
        sys.exit(2)
    return value


def main() -> int:
    config = ChatwootClientConfig(
        base_url=_require("CHATWOOT_BASE_URL"),
        account_id=_require("CHATWOOT_ACCOUNT_ID"),
        api_token=_require("CHATWOOT_API_ACCESS_TOKEN"),
    )
    client = ChatwootClient(config)
    payload = client.list_inboxes()
    items = payload.get("payload") or payload.get("data") or []
    web_items = []
    for item in items:
        channel_type = item.get("channel_type")
        if isinstance(channel_type, str) and channel_type.startswith("Channel::"):
            channel_type = channel_type.replace("Channel::", "", 1)
        if channel_type == "WebWidget":
            web_items.append(item)
    print(json.dumps({"count": len(items), "webwidget": web_items}, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
