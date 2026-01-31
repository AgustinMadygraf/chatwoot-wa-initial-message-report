import pytest

from src.infrastructure.chatwoot_api.chatwoot_http import ChatwootHTTPAdapter


class FakeClient:
    def __init__(self):
        self.calls = []

    async def post_json(self, url, headers, body):
        self.calls.append((url, headers, body))
        return 202, "accepted"


@pytest.mark.anyio
async def test_chatwoot_adapter_sends_message():
    client = FakeClient()
    adapter = ChatwootHTTPAdapter(
        base_url="https://example.com",
        token="token",
        client=client,
    )
    status, text = await adapter.send_message(1, 2, "hola")
    assert status == 202
    assert text == "accepted"
    assert client.calls
    url, headers, body = client.calls[0]
    assert url.endswith("/api/v1/accounts/1/conversations/2/messages")
    assert headers["api_access_token"] == "token"
    assert body["content"] == "hola"


@pytest.mark.anyio
async def test_chatwoot_adapter_requires_base_url(monkeypatch):
    from src.shared import config

    monkeypatch.setattr(config, "CHATWOOT_BASE_URL", "")
    adapter = ChatwootHTTPAdapter(base_url="", token="x", client=FakeClient())
    with pytest.raises(RuntimeError):
        await adapter.send_message(1, 2, "hola")
