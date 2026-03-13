import unittest

import httpx

from src.infrastructure.requests.http_transport import (
    HttpTimeoutError,
    HttpTransportError,
    HttpxSyncTransport,
)


class HttpTransportTest(unittest.TestCase):
    def test_httpx_transport_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(str(request.url), "https://example.com/test?page=1")
            self.assertEqual(request.headers.get("api_access_token"), "token")
            return httpx.Response(200, json={"ok": True})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        transport = HttpxSyncTransport(client=client)

        response = transport.get(
            "https://example.com/test",
            headers={"api_access_token": "token"},
            params={"page": 1},
            timeout=5.0,
            verify=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})

    def test_httpx_transport_maps_timeout_exception(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        transport = HttpxSyncTransport(client=client)

        with self.assertRaises(HttpTimeoutError):
            transport.get(
                "https://example.com/test",
                headers={"api_access_token": "token"},
                params=None,
                timeout=5.0,
                verify=True,
            )

    def test_httpx_transport_maps_generic_http_error(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ProtocolError("boom")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        transport = HttpxSyncTransport(client=client)

        with self.assertRaises(HttpTransportError):
            transport.get(
                "https://example.com/test",
                headers={"api_access_token": "token"},
                params=None,
                timeout=5.0,
                verify=True,
            )


if __name__ == "__main__":
    unittest.main()
