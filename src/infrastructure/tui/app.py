from __future__ import annotations

import asyncio
from typing import Callable, Iterable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import DataTable, Footer, Header, Static

from infrastructure.pymysql.fetchers import (
    fetch_accounts,
    fetch_conversations,
    fetch_inboxes,
    fetch_messages,
)
from shared.config import get_env
from shared.logger import get_logger


class Dataset:
    def __init__(
        self,
        title: str,
        columns: list[tuple[str, int, str]],
        fetcher: Callable[[], Iterable[dict]],
    ) -> None:
        self.title = title
        self.columns = columns
        self.fetcher = fetcher


def _account_id() -> int:
    value = get_env("CHATWOOT_ACCOUNT_ID")
    if not value:
        raise ValueError("Missing CHATWOOT_ACCOUNT_ID for inboxes")
    return int(value)


DATASETS: dict[str, Dataset] = {
    "accounts": Dataset(
        "CUENTAS",
        [
            ("ID", 6, "id"),
            ("NAME", 18, "name"),
            ("STATUS", 10, "status"),
            ("LOCAL", 6, "locale"),
            ("DOMAIN", 18, "domain"),
            ("SUPPORT_EMAIL", 24, "support_email"),
            ("CREATED_AT", 19, "created_at"),
            ("LATEST_CH", 10, "latest_chatwoot_version"),
        ],
        fetch_accounts,
    ),
    "inboxes": Dataset(
        "INBOXES",
        [
            ("ID", 6, "id"),
            ("ACCOUNT", 10, "account_id"),
            ("NAME", 18, "name"),
            ("CHANNEL", 18, "channel_type"),
            ("ADDRESS", 18, "address"),
            ("LAST_SYNCED", 19, "last_synced_at"),
        ],
        lambda: fetch_inboxes(_account_id()),
    ),
    "conversations": Dataset(
        "CONVERSACIONES",
        [
            ("ID", 6, "id"),
            ("INBOX", 8, "inbox_id"),
            ("STATUS", 10, "status"),
            ("SENDER_ID", 10, "meta__sender__id"),
            ("SENDER_NAME", 16, "meta__sender__name"),
            ("CREATED_AT", 19, "created_at"),
            ("LAST_ACTIVITY", 19, "last_activity_at"),
        ],
        fetch_conversations,
    ),
    "messages": Dataset(
        "MENSAJES",
        [
            ("ID", 7, "id"),
            ("CONVO", 8, "conversation_id"),
            ("INBOX", 8, "inbox_id"),
            ("MSG_TYPE", 8, "message_type"),
            ("SENDER_TYPE", 10, "sender_type"),
            ("SENDER_NAME", 14, "sender__name"),
            ("CREATED_AT", 19, "created_at"),
            ("CONTENT", 28, "content"),
        ],
        fetch_messages,
    ),
}


class As400App(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    Header, Footer {
        dock: top;
    }
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("f1", "show_help", "Help"),
        Binding("f3", "quit", "Salir"),
        Binding("f5", "refresh", "Refresh"),
        Binding("f8", "next_page", "Siguiente"),
        Binding("f9", "prev_page", "Anterior"),
        Binding("1", "accounts", "Cuentas"),
        Binding("2", "inboxes", "Inboxes"),
        Binding("3", "conversations", "Conversaciones"),
        Binding("4", "messages", "Mensajes"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.logger = get_logger("tui")
        self.current_dataset: Dataset | None = None
        self.rows: list[dict[str, object]] = []
        self.page = 0
        self.current_key: str | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, tall=False, id="header")
        yield Container(DataTable(id="table"), Static("", id="status"))
        yield Footer()

    async def on_mount(self) -> None:
        await self.load_dataset("accounts")

    async def load_dataset(self, key: str) -> None:
        dataset = DATASETS[key]
        self.current_dataset = dataset
        self.current_key = key
        self.rows = list(await asyncio.to_thread(dataset.fetcher))
        self.page = 0
        self._refresh_table()
        await self.query_one(Static).update(
            f"{dataset.title} | {len(self.rows)} filas | {datetime.now():%Y-%m-%d %H:%M:%S}"
        )

    def _refresh_table(self) -> None:
        if self.current_dataset is None:
            return
        table = self.query_one(DataTable)
        table.clear(columns=True)
        for header, width, _ in self.current_dataset.columns:
            table.add_column(header, width=width, min_width=width, max_width=width)
        page_size = max(5, self.size.height - 8)
        start = self.page * page_size
        end = start + page_size
        table.cursor_type = "row"
        for row_data in self.rows[start:end]:
            row = []
            for _, _, key in self.current_dataset.columns:
                value = row_data.get(key, "")
                row.append(str(value))
            table.add_row(*row)

    async def action_accounts(self) -> None:
        await self.load_dataset("accounts")

    async def action_inboxes(self) -> None:
        await self.load_dataset("inboxes")

    async def action_conversations(self) -> None:
        await self.load_dataset("conversations")

    async def action_messages(self) -> None:
        await self.load_dataset("messages")

    async def action_refresh(self) -> None:
        if self.current_key:
            await self.load_dataset(self.current_key)

    def action_next_page(self) -> None:
        if not self.rows or self.current_dataset is None:
            return
        page_size = max(5, self.size.height - 8)
        total_pages = (len(self.rows) + page_size - 1) // page_size
        if self.page < total_pages - 1:
            self.page += 1
            self._refresh_table()

    def action_prev_page(self) -> None:
        if self.page > 0:
            self.page -= 1
            self._refresh_table()

    def action_show_help(self) -> None:
        status = self.query_one(Static, id="status")
        status.update("F1=Help  F3=Salir  F5=Refresh  F8=Siguiente  F9=Anterior")
