import httpx
import pytest

from src.interface_adapter.presenters.webhook_api import app


@pytest.mark.anyio
async def test_webhook_rejects_bad_secret(monkeypatch):
    from src.infrastructure.settings import config

    monkeypatch.setattr(config, "WEBHOOK_SECRET", "expected")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post(
            "/webhook/bad",
            json={"event": "message_created", "message_type": "incoming"},
        )
        assert resp.status_code == 401


@pytest.mark.anyio
async def test_webhook_accepts_incoming(monkeypatch):
    from src.infrastructure.settings import config

    monkeypatch.setattr(config, "WEBHOOK_SECRET", "expected")
    monkeypatch.setattr(config, "CHATWOOT_BASE_URL", "https://example.com")
    monkeypatch.setattr(config, "CHATWOOT_BOT_TOKEN", "token")

    from src.infrastructure.requests import chatwoot_gateway

    async def _fake_send(self, account_id, conversation_id, content):
        return 200, "ok"

    monkeypatch.setattr(chatwoot_gateway.ChatwootRequestsGateway, "send_message", _fake_send)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "event": "message_created",
            "message_type": "incoming",
            "account": {"id": 1},
            "conversation": {"id": 2},
            "content": "hola",
        }
        resp = await client.post("/webhook/expected", json=payload)
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
