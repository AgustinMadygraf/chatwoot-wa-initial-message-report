import unittest
from unittest.mock import patch

from src.infrastructure.requests.chatwoot_fastapi_proxy_client import (
    ChatwootFastApiProxyClient,
)
from src.infrastructure.requests.chatwoot_requests_gateway import ChatwootRequestsGateway
from src.infrastructure.requests.sensitive_data_sanitizer import sanitize_payload
from src.infrastructure.settings.env_settings import ChatwootSettings


class _FakeResponse:
    def __init__(self, status_code: int, payload: object, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = {"content-type": "application/json"}

    def json(self) -> object:
        return self._payload


class _RecordingSyncTransport:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.calls: list[dict[str, object]] = []

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, object] | None,
        timeout: float,
        verify: bool | str,
    ) -> _FakeResponse:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": timeout,
                "verify": verify,
            }
        )
        return self._response


class _RecordingAsyncTransport:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.calls: list[dict[str, object]] = []

    async def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, object] | None,
        timeout: float,
        verify: bool | str,
    ) -> _FakeResponse:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": timeout,
                "verify": verify,
            }
        )
        return self._response


def _settings() -> ChatwootSettings:
    return ChatwootSettings(
        base_url="https://chatwoot.example.com",
        account_id=7,
        api_access_token="token-123",
        timeout_seconds=9.0,
        tls_verify=True,
    )


class RequestsArchitectureTest(unittest.IsolatedAsyncioTestCase):
    def test_sanitize_payload_masks_sensitive_keys_case_insensitive(self) -> None:
        payload = {
            "API_KEY": "abcd1234",
            "nested": {"Authorization": "Bearer secret-token"},
        }

        sanitized = sanitize_payload(payload)

        self.assertEqual(sanitized["API_KEY"], "ab...34")
        self.assertEqual(sanitized["nested"]["Authorization"], "Be...en")

    async def test_proxy_client_uses_injected_transport(self) -> None:
        response = _FakeResponse(
            status_code=200,
            payload={"payload": [{"id": 1}], "meta": {"count": 1, "current_page": 1}},
        )
        transport = _RecordingAsyncTransport(response)
        client = ChatwootFastApiProxyClient(settings=_settings(), transport=transport)

        result = await client.get_contacts(account_id=7, page="1")

        self.assertEqual(result["meta"]["count"], 1)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(
            transport.calls[0]["url"],
            "https://chatwoot.example.com/api/v1/accounts/7/contacts",
        )

    async def test_requests_gateway_uses_injected_transport(self) -> None:
        response = _FakeResponse(status_code=200, payload=[])
        transport = _RecordingSyncTransport(response)
        gateway = ChatwootRequestsGateway(settings=_settings(), transport=transport)

        with patch(
            "src.infrastructure.requests.chatwoot_requests_gateway.check_dns",
            return_value=(True, "dns ok"),
        ), patch(
            "src.infrastructure.requests.chatwoot_requests_gateway.check_tcp",
            return_value=(True, "tcp ok"),
        ):
            result = gateway.validate_connection()

        self.assertTrue(result.ok)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(
            transport.calls[0]["url"],
            "https://chatwoot.example.com/api/v1/accounts/7/inboxes",
        )


if __name__ == "__main__":
    unittest.main()
