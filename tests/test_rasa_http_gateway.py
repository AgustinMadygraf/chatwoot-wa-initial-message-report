import json

import pytest

from src.infrastructure.rasa.rasa_http import RasaHTTPGateway


class FakeClient:
    def __init__(self, status=200, text="[]"):
        self.status = status
        self.text = text
        self.calls = []

    async def post_json(self, url, headers, body):
        self.calls.append((url, headers, body))
        return self.status, self.text


@pytest.mark.anyio
async def test_rasa_gateway_parses_texts(monkeypatch):
    from src.shared import config

    monkeypatch.setattr(config, "RASA_REST_URL", "http://localhost:5005/webhooks/rest/webhook")
    payload = json.dumps([{"text": "hola"}, {"text": "mundo"}])
    client = FakeClient(status=200, text=payload)
    gateway = RasaHTTPGateway(client=client)
    texts = await gateway.send_message("conv-1", "hi")
    assert texts == ["hola", "mundo"]
    assert client.calls


@pytest.mark.anyio
async def test_rasa_gateway_handles_error_status(monkeypatch):
    from src.shared import config

    monkeypatch.setattr(config, "RASA_REST_URL", "http://localhost:5005/webhooks/rest/webhook")
    client = FakeClient(status=500, text="error")
    gateway = RasaHTTPGateway(client=client)
    with pytest.raises(RuntimeError):
        await gateway.send_message("conv-1", "hi")
