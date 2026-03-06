import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.responses import RedirectResponse

PAGE_SIZE = 15
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/accounts/{account_id}/inboxes")
def get_inboxes(
    account_id: int,
) -> list[dict[str, Any]]:
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
    request: Request,
    account_id: int,
    page: int | None = Query(default=None, ge=1),
) -> dict[str, Any]:
    if page is None:
        target_url = str(request.url.include_query_params(page=1))
        return RedirectResponse(url=target_url, status_code=307)

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
