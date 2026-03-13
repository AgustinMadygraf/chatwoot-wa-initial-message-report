"""
Path: src/infrastructure/requests/http_transport.py
"""

from collections.abc import Mapping
from typing import Any, Protocol

import httpx
import requests


class HttpTransportError(Exception):
    """Base error for HTTP transport adapters."""


class HttpTimeoutError(HttpTransportError):
    pass


class HttpTlsError(HttpTransportError):
    pass


class HttpConnectionError(HttpTransportError):
    pass


class HttpResponse(Protocol):
    status_code: int
    text: str
    headers: Mapping[str, str]

    def json(self) -> Any:
        ...


class SyncHttpTransport(Protocol):
    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        timeout: float,
        verify: bool | str,
    ) -> HttpResponse:
        ...


class AsyncHttpTransport(Protocol):
    async def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        timeout: float,
        verify: bool | str,
    ) -> HttpResponse:
        ...


class HttpxSyncTransport:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        timeout: float,
        verify: bool | str,
    ) -> HttpResponse:
        try:
            if self._client is not None:
                return self._client.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=timeout,
                )
            return httpx.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
                verify=verify,
            )
        except httpx.TimeoutException as exc:
            raise HttpTimeoutError(str(exc)) from exc
        except httpx.ConnectError as exc:
            message = str(exc).upper()
            if "SSL" in message or "CERT" in message or "TLS" in message:
                raise HttpTlsError(str(exc)) from exc
            raise HttpConnectionError(str(exc)) from exc
        except httpx.NetworkError as exc:
            raise HttpConnectionError(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HttpTransportError(str(exc)) from exc


class HttpxAsyncTransport:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        timeout: float,
        verify: bool | str,
    ) -> HttpResponse:
        try:
            if self._client is not None:
                return await self._client.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=timeout,
                )
            async with httpx.AsyncClient(verify=verify, timeout=timeout) as client:
                return await client.get(
                    url,
                    headers=headers,
                    params=params,
                )
        except httpx.TimeoutException as exc:
            raise HttpTimeoutError(str(exc)) from exc
        except httpx.ConnectError as exc:
            message = str(exc).upper()
            if "SSL" in message or "CERT" in message or "TLS" in message:
                raise HttpTlsError(str(exc)) from exc
            raise HttpConnectionError(str(exc)) from exc
        except httpx.NetworkError as exc:
            raise HttpConnectionError(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HttpTransportError(str(exc)) from exc


class RequestsHttpTransport:
    def __init__(self, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        timeout: float,
        verify: bool | str,
    ) -> HttpResponse:
        try:
            return self._session.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
                verify=verify,
            )
        except requests.exceptions.Timeout as exc:
            raise HttpTimeoutError(str(exc)) from exc
        except requests.exceptions.SSLError as exc:
            raise HttpTlsError(str(exc)) from exc
        except requests.exceptions.ConnectionError as exc:
            raise HttpConnectionError(str(exc)) from exc
        except requests.RequestException as exc:
            raise HttpTransportError(str(exc)) from exc
