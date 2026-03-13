import unittest

import httpx

from src.infrastructure.requests.http_transport import (
    HttpTimeoutError,
    HttpTransportError,
    HttpxAsyncTransport,
)


class HttpAsyncTransportTest(unittest.IsolatedAsyncioTestCase):
    async def test_httpx_async_transport_success(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(str(request.url), "https://example.com/test?page=1")
            self.assertEqual(request.headers.get("api_access_token"), "token")
            return httpx.Response(200, json={"ok": True})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        transport = HttpxAsyncTransport(client=client)

        response = await transport.get(
            "https://example.com/test",
            headers={"api_access_token": "token"},
            params={"page": 1},
            timeout=5.0,
            verify=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        await client.aclose()

    async def test_httpx_async_transport_maps_timeout_exception(self) -> None:
        async def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        transport = HttpxAsyncTransport(client=client)

        with self.assertRaises(HttpTimeoutError):
            await transport.get(
                "https://example.com/test",
                headers={"api_access_token": "token"},
                params=None,
                timeout=5.0,
                verify=True,
            )
        await client.aclose()

    async def test_httpx_async_transport_maps_generic_http_error(self) -> None:
        async def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ProtocolError("boom")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        transport = HttpxAsyncTransport(client=client)

        with self.assertRaises(HttpTransportError):
            await transport.get(
                "https://example.com/test",
                headers={"api_access_token": "token"},
                params=None,
                timeout=5.0,
                verify=True,
            )
        await client.aclose()


if __name__ == "__main__":
    unittest.main()
