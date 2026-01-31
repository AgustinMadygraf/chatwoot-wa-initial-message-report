from fastapi.testclient import TestClient

from src.interface_adapter.presenters.webhook_api import app


def test_webhook_rejects_bad_secret(monkeypatch):
    from src.shared import config

    monkeypatch.setattr(config, "WEBHOOK_SECRET", "expected")
    client = TestClient(app)
    resp = client.post("/webhook/bad", json={"event": "message_created", "message_type": "incoming"})
    assert resp.status_code == 401


def test_webhook_accepts_incoming(monkeypatch):
    from src.shared import config

    monkeypatch.setattr(config, "WEBHOOK_SECRET", "expected")
    monkeypatch.setattr(config, "CHATWOOT_BASE_URL", "https://example.com")
    monkeypatch.setattr(config, "CHATWOOT_BOT_TOKEN", "token")

    from src.infrastructure.chatwoot_api import chatwoot_http
    from src.infrastructure.rasa import rasa_http

    async def _fake_send(self, account_id, conversation_id, content):
        return 200, "ok"

    monkeypatch.setattr(chatwoot_http.ChatwootHTTPAdapter, "send_message", _fake_send)

    async def _fake_rasa(self, sender_id, text):
        return ["respuesta"]

    monkeypatch.setattr(rasa_http.RasaHTTPGateway, "send_message", _fake_rasa)

    client = TestClient(app)
    payload = {
        "event": "message_created",
        "message_type": "incoming",
        "account": {"id": 1},
        "conversation": {"id": 2},
        "content": "hola",
    }
    resp = client.post("/webhook/expected", json=payload)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
