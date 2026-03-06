from __future__ import annotations

from types import SimpleNamespace

import pytest
from requests import RequestException

from infrastructure.cli import ui
from infrastructure.cli.tui import app as tui_app
from use_cases.conversations_sync import _pick_address_for_debug, sync_conversations
from use_cases.inboxes_sync import sync_inboxes
from use_cases.messages_sync import _next_page, sync_messages


def test_ui_pagination_and_helpers(monkeypatch) -> None:
    rows = [{"id": i, "name": f"name-{i}"} for i in range(12)]
    keys = iter(["N", "P", "F5", "Q"])
    monkeypatch.setattr(ui, "_is_tty", lambda: True)
    monkeypatch.setattr(ui, "_read_key", lambda: next(keys))
    monkeypatch.setattr(ui, "_page_size", lambda: 5)
    # cover page iteration path
    ui._render_table_paginated(
        ui._console(),
        "TITLE",
        "SRC",
        [("id", 5), ("name", 10)],
        rows,
        ui._row_from_raw,
    )
    assert ui._compute_width([("a", 1), ("b", 2)]) > 0


def test_ui_read_key_fallback(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda: "n")
    assert ui._read_key() == "N"
    monkeypatch.setattr("builtins.input", lambda: "")
    assert ui._read_key() == ""


def test_ui_render_misc(monkeypatch) -> None:
    monkeypatch.setattr(ui, "_terminal_size", lambda: SimpleNamespace(columns=30, lines=8))
    assert ui._screen_width() == 40
    assert ui._page_size() == 5
    cols = ui._fit_columns([("a", 20), ("b", 20)], 20)
    assert len(cols) == 2
    assert ui._truncate("abcd", 2) == "ab"
    assert ui._fit_text("abcdef", 3) == "abc"


def test_tui_account_id_and_actions(monkeypatch) -> None:
    monkeypatch.setattr(tui_app, "get_env", lambda _n: None)
    with pytest.raises(ValueError):
        tui_app._account_id()
    monkeypatch.setattr(tui_app, "get_env", lambda _n: "12")
    assert tui_app._account_id() == 12

    app = tui_app.As400App()
    called = {"key": None}

    async def _fake_load_dataset(key: str) -> None:
        called["key"] = key

    app.load_dataset = _fake_load_dataset  # type: ignore[assignment]
    import asyncio

    asyncio.run(app.action_accounts())
    assert called["key"] == "accounts"


def test_tui_refresh_paging_and_help(monkeypatch) -> None:
    app = tui_app.As400App()
    table_calls = {"refresh": 0}

    class _Table:
        def clear(self, columns=True):
            return None

        def add_column(self, *_a, **_k):
            return None

        def add_row(self, *_a, **_k):
            return None

    class _Status:
        def __init__(self):
            self.last = ""

        def update(self, text):
            self.last = str(text)
            return None

    status = _Status()
    table = _Table()

    def _query_one(selector=None, cls=None):
        if selector == "#status":
            return status
        return table

    app.query_one = _query_one  # type: ignore[assignment]
    monkeypatch.setattr(tui_app.As400App, "size", property(lambda self: SimpleNamespace(height=20)))
    app.current_dataset = SimpleNamespace(columns=[("ID", 3, "id")])
    app.rows = [{"id": i} for i in range(20)]
    app.current_key = None
    app.action_next_page()
    assert app.page == 1
    app.action_prev_page()
    assert app.page == 0
    app.action_show_help()
    assert "F1=Help" in status.last
    # refresh with no current key should be no-op
    import asyncio

    asyncio.run(app.action_refresh())
    # now with key should delegate
    async def _fake_load_dataset(_key: str) -> None:
        table_calls["refresh"] += 1

    app.load_dataset = _fake_load_dataset  # type: ignore[assignment]
    app.current_key = "accounts"
    asyncio.run(app.action_refresh())
    assert table_calls["refresh"] == 1


class _Repo:
    def __init__(self) -> None:
        self.rows = []

    def ensure_table(self) -> None:
        return None

    def upsert_conversation(self, row):
        self.rows.append(row)

    def upsert_inbox(self, row):
        self.rows.append(row)

    def upsert_message(self, row):
        self.rows.append(row)


def test_sync_conversations_edges() -> None:
    repo = _Repo()

    class _Client:
        def __init__(self):
            self.page = 0

        def list_conversations(self, *, page: int, per_page=None):
            self.page += 1
            if self.page == 1:
                raise RequestException("x")
            return {"payload": []}

    assert sync_conversations(_Client(), repo) == []
    assert _pick_address_for_debug({"meta": {"sender": {"name": "Ana"}}}) == "Ana"


def test_sync_inboxes_debug_and_extract(monkeypatch) -> None:
    repo = _Repo()

    class _Client:
        def list_inboxes(self):
            return {"data": [{"id": 1, "channel_type": "WebWidget", "website_url": "https://x"}]}

    monkeypatch.setenv("DEBUG_INBOXES", "1")
    out = sync_inboxes(_Client(), repo)
    assert out["total_upserted"] == 1
    monkeypatch.delenv("DEBUG_INBOXES", raising=False)


def test_sync_messages_edges() -> None:
    repo = _Repo()

    class _Client:
        def list_conversation_messages(self, *, conversation_id: int, page=None, per_page=None, before=None):
            if page == 1 or before is None:
                return {"payload": [{"id": 10, "conversation_id": conversation_id, "inbox_id": 1, "message_type": 5, "content": "x"}]}
            return {"payload": []}

    # repeated page ids then cursor fallback path
    result = sync_messages(_Client(), repo, conversation_ids=[7])
    assert result["total_upserted"] == 0
    assert _next_page({"meta": {"next_page": None}}, 1) is None
