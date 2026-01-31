import json

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.interface_adapter.controllers.webhook_controller import WebhookController
from src.shared import config


class DummyUseCase:
    def __init__(self, result):
        self.result = result
        self.payloads = []

    async def execute(self, payload):
        self.payloads.append(payload)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _make_request(payload: dict) -> Request:
    body = json.dumps(payload).encode("utf-8")

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/webhook/test",
        "headers": [],
    }
    return Request(scope, receive)


@pytest.mark.anyio
async def test_controller_rejects_bad_secret(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_SECRET", "expected")
    controller = WebhookController(DummyUseCase({"ok": True}))
    req = _make_request({"event": "message_created", "message_type": "incoming"})
    with pytest.raises(HTTPException) as exc:
        await controller.handle("bad", req)
    assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_controller_calls_usecase(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_SECRET", "expected")
    usecase = DummyUseCase({"ok": True})
    controller = WebhookController(usecase)
    payload = {"event": "message_created", "message_type": "incoming"}
    req = _make_request(payload)
    result = await controller.handle("expected", req)
    assert result == {"ok": True}
    assert usecase.payloads == [payload]


@pytest.mark.anyio
async def test_controller_propagates_usecase_error(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_SECRET", "expected")
    usecase = DummyUseCase(RuntimeError("boom"))
    controller = WebhookController(usecase)
    req = _make_request({"event": "message_created", "message_type": "incoming"})
    with pytest.raises(RuntimeError):
        await controller.handle("expected", req)
