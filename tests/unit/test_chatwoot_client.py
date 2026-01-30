from __future__ import annotations

from typing import Any

import infrastructure.chatwoot_api.client as client_mod


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = "ERR"

    def raise_for_status(self) -> None:
        if not self.ok:
            raise RuntimeError("bad")

    def json(self) -> dict[str, Any]:
        return self._payload


def test_chatwoot_client_list_and_check(monkeypatch) -> None:
    def _get(*_args, **_kwargs):
        return FakeResponse({"payload": []})

    monkeypatch.setattr(client_mod.requests, "get", _get)
    cfg = client_mod.ChatwootClientConfig(
        base_url="https://chatwoot.local", account_id="1", api_token="t"
    )
    client = client_mod.ChatwootClient(cfg)
    assert client.list_inboxes() == {"payload": []}
    assert client.list_conversations(page=1) == {"payload": []}
    assert client.list_conversation_messages(conversation_id=1, page=1) == {"payload": []}
    assert client.get_account_details() == {"payload": []}


def test_chatwoot_check_connection_error(monkeypatch) -> None:
    def _get(*_args, **_kwargs):
        return FakeResponse({"error": "x"}, status_code=500)

    monkeypatch.setattr(client_mod.requests, "get", _get)
    cfg = client_mod.ChatwootClientConfig(
        base_url="https://chatwoot.local", account_id="1", api_token="t"
    )
    client = client_mod.ChatwootClient(cfg)
    result = client.check_connection()
    assert result["ok"] is False
