import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query

PAGE_SIZE = 15
DEFAULT_TOKEN = "local-token"
ROOT_DIR = Path(__file__).resolve().parents[3]
CONTACTS_FIXTURE = ROOT_DIR / "data" / "all_contacts.json"


def _load_contacts() -> list[dict[str, Any]]:
    if CONTACTS_FIXTURE.exists():
        raw = json.loads(CONTACTS_FIXTURE.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
    return []


CONTACTS = _load_contacts()
app = FastAPI(title="Chatwoot Local Contract Mock", version="1.0.0")


def _require_token(api_access_token: str | None) -> None:
    expected = os.getenv("CHATWOOT_MOCK_API_ACCESS_TOKEN", DEFAULT_TOKEN)
    if not api_access_token:
        raise HTTPException(status_code=401, detail="api_access_token requerido")
    if api_access_token != expected:
        raise HTTPException(status_code=403, detail="api_access_token invalido")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/accounts/{account_id}/inboxes")
def get_inboxes(
    account_id: int,
    api_access_token: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    _require_token(api_access_token)
    return [
        {
            "id": 2,
            "name": "Whatsapp API",
            "channel_type": "Channel::Whatsapp",
            "provider": "whatsapp_cloud",
            "account_id": account_id,
        }
    ]


@app.get("/api/v1/accounts/{account_id}/contacts")
def get_contacts(
    account_id: int,
    page: int = Query(default=1, ge=1),
    api_access_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_token(api_access_token)
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    payload = CONTACTS[start:end]
    return {
        "payload": payload,
        "meta": {
            "count": len(CONTACTS),
            "current_page": page,
            "account_id": account_id,
        },
    }
