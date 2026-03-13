"""
Path: src/infrastructure/fastapi/app.py
"""

from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import HTMLResponse

from src.interface_adapter.controllers.fastapi_proxy_controllers import (
    GetContactByIdController,
    GetContactsController,
    GetInboxByIdController,
    GetInboxesController,
)
from src.infrastructure.requests.chatwoot_fastapi_proxy_client import (
    ChatwootFastApiProxyClient,
)
from src.infrastructure.requests.http_transport import HttpxAsyncTransport
from src.infrastructure.settings.env_settings import ChatwootSettings, load_chatwoot_settings
from src.use_case.errors import ProxyGatewayError

_settings: ChatwootSettings | None = None
_proxy_client: ChatwootFastApiProxyClient | None = None
_async_http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _settings, _proxy_client, _async_http_client

    try:
        _settings = load_chatwoot_settings()
        _async_http_client = httpx.AsyncClient(
            timeout=_settings.timeout_seconds,
            verify=_settings.tls_verify,
        )
        _proxy_client = ChatwootFastApiProxyClient(
            _settings,
            transport=HttpxAsyncTransport(client=_async_http_client),
        )
    except Exception:
        _settings = None
        _proxy_client = None
        if _async_http_client is not None:
            await _async_http_client.aclose()
            _async_http_client = None

    try:
        yield
    finally:
        if _async_http_client is not None:
            await _async_http_client.aclose()
            _async_http_client = None


app = FastAPI(title="Chatwoot API Interface", version="2.1.0", lifespan=lifespan)


def _require_proxy_client() -> ChatwootFastApiProxyClient:
    if _proxy_client is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Configuracion Chatwoot invalida. Verifica .env: "
                "CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID, CHATWOOT_API_ACCESS_TOKEN."
            ),
        )
    return _proxy_client


def _raise_http_error(error: ProxyGatewayError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _human_href(path: str) -> str:
    href = (
        path.replace("{account_id}", "1")
        .replace("{id}", "21")
        .replace("{inbox_id}", "2")
    )
    if "contacts" in href and "{id}" not in path and "?" not in href:
        href = f"{href}?page=1"
    return href


@app.get("/health")
def health() -> dict[str, str]:
    if _settings is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Configuracion Chatwoot invalida. Verifica .env: "
                "CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID, CHATWOOT_API_ACCESS_TOKEN."
            ),
        )
    return {
        "status": "ok",
        "mode": "proxy",
        "chatwoot_base_url": _settings.base_url,
    }


@app.get("/")
def root(format: str = Query(default="human")) -> Any:
    endpoints: list[dict[str, object]] = []
    for route in app.routes:
        methods = sorted(
            method
            for method in (getattr(route, "methods", set()) or set())
            if method not in {"HEAD", "OPTIONS"}
        )
        path = getattr(route, "path", None)
        if not path:
            continue
        endpoints.append({"path": path, "methods": methods})

    endpoints.sort(key=lambda item: str(item["path"]))
    if format.lower() == "json":
        return {"count": len(endpoints), "endpoints": endpoints}

    lines = []
    for item in endpoints:
        methods = ", ".join(item["methods"]) if item["methods"] else "-"
        path = str(item["path"])
        href = _human_href(path)
        lines.append(
            f"<li><code>{methods}</code> "
            f"<a href='{href}'><code>{path}</code></a></li>"
        )

    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Endpoints</title>"
        "<style>"
        "body{font-family:Arial,sans-serif;max-width:900px;margin:32px auto;padding:0 16px;}"
        "code{background:#f3f4f6;padding:2px 6px;border-radius:4px;}"
        "li{margin:10px 0;}h1{margin-bottom:8px;}p{color:#444;}a{text-decoration:none;}"
        "</style></head><body>"
        "<h1>Endpoints disponibles</h1>"
        "<p>Vista humana. Para formato JSON usa <code>/?format=json</code>.</p>"
        "<p>Los links usan <code>account_id=1</code> por defecto.</p>"
        f"<p>Total: <strong>{len(endpoints)}</strong></p>"
        "<ul>"
        + "".join(lines)
        + "</ul></body></html>"
    )
    return HTMLResponse(content=html)


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/api/v1/accounts/{account_id}/inboxes")
async def get_inboxes(account_id: int) -> Any:
    client = _require_proxy_client()
    controller = GetInboxesController(client=client)
    try:
        return await controller.run(account_id=account_id)
    except ProxyGatewayError as error:
        _raise_http_error(error)


@app.get("/api/v1/accounts/{account_id}/inboxes/{inbox_id}")
async def get_inbox_by_id(account_id: int, inbox_id: int) -> dict[str, Any]:
    client = _require_proxy_client()
    controller = GetInboxByIdController(client=client)
    try:
        return await controller.run(account_id=account_id, inbox_id=inbox_id)
    except ProxyGatewayError as error:
        _raise_http_error(error)


@app.get("/api/v1/accounts/{account_id}/contacts")
async def get_contacts(
    account_id: int,
    page: str | None = Query(default=None),
) -> dict[str, Any]:
    client = _require_proxy_client()
    controller = GetContactsController(client=client)
    try:
        return await controller.run(account_id=account_id, page=page)
    except ProxyGatewayError as error:
        _raise_http_error(error)


@app.get("/api/v1/accounts/{account_id}/contacts/{id}")
async def get_contact_by_id(account_id: int, id: int) -> dict[str, Any]:
    client = _require_proxy_client()
    controller = GetContactByIdController(client=client)
    try:
        return await controller.run(account_id=account_id, contact_id=id)
    except ProxyGatewayError as error:
        _raise_http_error(error)
