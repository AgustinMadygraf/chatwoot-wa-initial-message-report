import unittest

from fastapi.testclient import TestClient

from src.infrastructure.fastapi import app as app_module
from src.infrastructure.settings.env_settings import ChatwootSettings


class _DummyProxyClient:
    def enforce_account_id(self, _account_id: int) -> None:
        return None

    async def get_inboxes(self, _account_id: int):
        return [{"id": 1}]

    async def get_inbox_by_id(self, _account_id: int, _inbox_id: int):
        return {"payload": {"id": 1}}

    async def get_contacts(self, _account_id: int, _page: str | None):
        return {"payload": [{"id": 10}], "meta": {"count": 1}}

    async def get_contact_by_id(self, _account_id: int, _contact_id: int):
        return {"payload": {"id": 10}}


def _settings() -> ChatwootSettings:
    return ChatwootSettings(
        base_url="https://chatwoot.example.com",
        account_id=7,
        api_access_token="token-123",
        proxy_api_key="proxy-secret",
        timeout_seconds=9.0,
        tls_verify=True,
    )


class FastApiProxyAuthTest(unittest.TestCase):
    def setUp(self) -> None:
        self._original_settings = app_module._settings
        self._original_proxy_client = app_module._proxy_client

    def tearDown(self) -> None:
        app_module._settings = self._original_settings
        app_module._proxy_client = self._original_proxy_client

    def test_proxy_endpoint_requires_api_key(self) -> None:
        with TestClient(app_module.app) as client:
            app_module._settings = _settings()
            app_module._proxy_client = _DummyProxyClient()
            response = client.get("/api/v1/accounts/7/inboxes")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Unauthorized")

    def test_proxy_endpoint_rejects_invalid_api_key(self) -> None:
        with TestClient(app_module.app) as client:
            app_module._settings = _settings()
            app_module._proxy_client = _DummyProxyClient()
            response = client.get(
                "/api/v1/accounts/7/inboxes",
                headers={"X-Proxy-Api-Key": "wrong-key"},
            )

        self.assertEqual(response.status_code, 401)

    def test_proxy_endpoint_accepts_valid_api_key(self) -> None:
        with TestClient(app_module.app) as client:
            app_module._settings = _settings()
            app_module._proxy_client = _DummyProxyClient()
            response = client.get(
                "/api/v1/accounts/7/inboxes",
                headers={"X-Proxy-Api-Key": "proxy-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": 1}])


if __name__ == "__main__":
    unittest.main()
