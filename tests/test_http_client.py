import pytest

from src.infrastructure.httpx import http_client


class DummyResponse:
    def __init__(self, status_code=200, text="ok"):
        self.status_code = status_code
        self.text = text


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None):
        self.calls.append((url, headers, json))
        return DummyResponse(201, "created")


@pytest.mark.anyio
async def test_http_client_post_json(monkeypatch):
    monkeypatch.setattr(http_client.httpx, "AsyncClient", DummyAsyncClient)
    client = http_client.HttpxClient(timeout=5)
    status, text = await client.post_json(
        "https://example.com",
        headers={"h": "v"},
        body={"a": 1},
    )
    assert status == 201
    assert text == "created"
