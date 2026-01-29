from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rich import box
from rich.console import Console, Group
from rich.table import Table
from rich.text import Text

SCREEN_WIDTH = 80


def print_contacts_table(contacts, include_first_message: bool = False) -> None:
    console = Console()
    if include_first_message:
        columns = [
            ("id", 6),
            ("name", 16),
            ("first_message", 48),
        ]
    else:
        columns = [
            ("id", 6),
            ("name", 24),
            ("phone_number", 16),
            ("email", 28),
            ("created_at", 19),
            ("last_activity_at", 19),
        ]
    width = _compute_width(columns)
    _render_header(
        console,
        width,
        "LISTADO CONTACTOS",
        "CHATWOOT API" if include_first_message else "MYSQL",
    )
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
    )
    for label, col_width in columns:
        table.add_column(
            label.upper(),
            width=col_width,
            min_width=col_width,
            max_width=col_width,
            overflow="ellipsis",
            no_wrap=True,
            style="green",
        )
    for col in table.columns:
        col.style = "green"
    table.columns[0].style = "bold green"
    for contact in contacts:
        row = []
        for key, col_width in columns:
            raw = contact.get(key)
            value = _format_datetime_cell(key, raw)
            value = _clean_cell(value)
            row.append(_truncate(value, col_width))
        table.add_row(*row)
    console.print(table)
    _render_footer(console, width)


def print_contacts_by_channel_table(contacts) -> None:
    console = Console()
    columns = [
        ("id", 6),
        ("name", 12),
        ("phone_number", 14),
        ("inbox_name", 14),
        ("provider", 10),
        ("channel_type", 12),
        ("created_at", 19),
        ("last_activity_at", 19),
    ]
    width = _compute_width(columns)
    _render_header(console, width, "CONTACTOS POR CANAL", "MYSQL")
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
    )
    for label, col_width in columns:
        table.add_column(
            label.upper(),
            width=col_width,
            min_width=col_width,
            max_width=col_width,
            overflow="ellipsis",
            no_wrap=True,
            style="green",
        )
    for col in table.columns:
        col.style = "green"
    table.columns[0].style = "bold green"
    for contact in contacts:
        row = []
        for key, col_width in columns:
            raw = contact.get(key)
            value = _format_datetime_cell(key, raw)
            value = _clean_cell(value)
            row.append(_truncate(value, col_width))
        table.add_row(*row)
    console.print(table)
    _render_footer(console, width)


def print_inboxes_table(inboxes) -> None:
    console = Console()
    columns = [
        ("id", 6),
        ("name", 18),
        ("channel_type", 18),
        ("provider", 14),
        ("channel_id", 10),
        ("phone_number", 16),
        ("email", 20),
        ("website_token", 12),
    ]
    width = _compute_width(columns)
    _render_header(console, width, "INBOXES", "MYSQL")
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
    )
    for label, col_width in columns:
        table.add_column(
            label.upper(),
            width=col_width,
            min_width=col_width,
            max_width=col_width,
            overflow="ellipsis",
            no_wrap=True,
            style="green",
        )
    for col in table.columns:
        col.style = "green"
    table.columns[0].style = "bold green"
    for inbox in inboxes:
        row = []
        for key, col_width in columns:
            raw = inbox.get(key)
            value = "" if raw is None else str(raw)
            value = _clean_cell(value)
            row.append(_truncate(value, col_width))
        table.add_row(*row)
    console.print(table)
    _render_footer(console, width)


def print_accounts_table(accounts) -> None:
    console = Console()
    columns = [
        ("id", 6),
        ("name", 18),
        ("status", 10),
        ("locale", 6),
        ("domain", 18),
        ("support_email", 24),
        ("created_at", 19),
        ("latest_chatwoot_version", 10),
    ]
    width = _compute_width(columns)
    _render_header(console, width, "CUENTAS", "MYSQL")
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
    )
    for label, col_width in columns:
        table.add_column(
            label.upper(),
            width=col_width,
            min_width=col_width,
            max_width=col_width,
            overflow="ellipsis",
            no_wrap=True,
            style="green",
        )
    for col in table.columns:
        col.style = "green"
    table.columns[0].style = "bold green"
    for account in accounts:
        row = []
        for key, col_width in columns:
            raw = account.get(key)
            value = _format_datetime_cell(key, raw)
            value = _clean_cell(value)
            row.append(_truncate(value, col_width))
        table.add_row(*row)
    console.print(table)
    _render_footer(console, width)


def print_conversations_table(conversations) -> None:
    console = Console()
    columns = [
        ("id", 6),
        ("inbox_id", 8),
        ("status", 10),
        ("meta__sender__id", 10),
        ("meta__sender__name", 16),
        ("created_at", 19),
        ("last_activity_at", 19),
    ]
    width = _compute_width(columns)
    _render_header(console, width, "CONVERSACIONES", "MYSQL")
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
    )
    for label, col_width in columns:
        table.add_column(
            label.upper(),
            width=col_width,
            min_width=col_width,
            max_width=col_width,
            overflow="ellipsis",
            no_wrap=True,
            style="green",
        )
    for col in table.columns:
        col.style = "green"
    table.columns[0].style = "bold green"
    for convo in conversations:
        row = []
        for key, col_width in columns:
            raw = convo.get(key)
            value = _format_datetime_cell(key, raw)
            value = _clean_cell(value)
            row.append(_truncate(value, col_width))
        table.add_row(*row)
    console.print(table)
    _render_footer(console, width)


def print_messages_table(messages) -> None:
    console = Console()
    columns = [
        ("id", 7),
        ("conversation_id", 8),
        ("inbox_id", 8),
        ("message_type", 8),
        ("sender_type", 10),
        ("sender__name", 14),
        ("created_at", 19),
        ("content", 28),
    ]
    width = _compute_width(columns)
    _render_header(console, width, "MENSAJES", "MYSQL")
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
    )
    for label, col_width in columns:
        table.add_column(
            label.upper(),
            width=col_width,
            min_width=col_width,
            max_width=col_width,
            overflow="ellipsis",
            no_wrap=True,
            style="green",
        )
    for col in table.columns:
        col.style = "green"
    table.columns[0].style = "bold green"
    for msg in messages:
        row = []
        for key, col_width in columns:
            raw = msg.get(key)
            value = _format_datetime_cell(key, raw)
            value = _clean_cell(value)
            row.append(_truncate(value, col_width))
        table.add_row(*row)
    console.print(table)
    _render_footer(console, width)


def print_health_screen(results: dict) -> None:
    console = Console()
    columns = [
        ("service", 10),
        ("status", 6),
        ("detail", 54),
    ]
    width = SCREEN_WIDTH
    _render_header(console, width, "ESTADO GENERAL", "CLI")
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
    )
    for label, col_width in columns:
        table.add_column(
            label.upper(),
            width=col_width,
            min_width=col_width,
            max_width=col_width,
            overflow="ellipsis",
            no_wrap=True,
            style="green",
        )
    table.columns[0].style = "green"
    table.columns[1].style = "bold green" if results.get("ok") else "bold yellow"
    table.columns[2].style = "green"
    for key in ("chatwoot", "mysql"):
        item = results[key]
        status = "OK" if item["ok"] else "ERROR"
        detail = _clean_cell(item.get("error") or "")
        table.add_row(key, status, _truncate(detail, columns[2][1]))
    console.print(table)
    _render_footer(console, width)


def print_sync_screen(
    stats: dict,
    *,
    total_in_db: int = 0,
    started_at: datetime | None = None,
) -> None:
    console = Console()
    columns = [
        ("metric", 36),
        ("value", 37),
    ]
    width = SCREEN_WIDTH
    _render_header(console, width, "SYNC CONTACTOS", "MYSQL")
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
    )
    for label, col_width in columns:
        table.add_column(
            label.upper(),
            width=col_width,
            min_width=col_width,
            max_width=col_width,
            overflow="ellipsis",
            no_wrap=True,
            style="green",
        )
    table.columns[0].style = "green"
    table.columns[1].style = "bold green"
    table.add_row("listados", str(stats.get("total_listed", 0)))
    table.add_row("upserted", str(stats.get("total_upserted", 0)))
    table.add_row("skipped", str(stats.get("total_skipped", 0)))
    table.add_row("total_db", str(total_in_db))
    console.print(table)
    elapsed = None
    if started_at:
        elapsed = str(datetime.now() - started_at).split(".", maxsplit=1)[0]
    _render_footer(console, width, elapsed=elapsed)


def build_sync_progress_screen(stats: dict, *, started_at: datetime | None = None) -> Group:
    columns = [
        ("metric", 36),
        ("value", 37),
    ]
    width = SCREEN_WIDTH
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
    )
    for label, col_width in columns:
        table.add_column(
            label.upper(),
            width=col_width,
            min_width=col_width,
            max_width=col_width,
            overflow="ellipsis",
            no_wrap=True,
            style="green",
        )
    table.columns[0].style = "green"
    table.columns[1].style = "bold green"
    rows = [
        ("fase", "phase"),
        ("contactos_pagina", "contacts_page"),
        ("contactos_listados", "contacts_listed"),
        ("contactos_upserted", "contacts_upserted"),
        ("contactos_skipped", "contacts_skipped"),
        ("accounts_upserted", "accounts_upserted"),
        ("inboxes_upserted", "inboxes_upserted"),
        ("conversaciones_pagina", "conversations_page"),
        ("conversaciones_upserted", "conversations_upserted"),
        ("mensajes_upserted", "messages_upserted"),
        ("mensajes_errores", "messages_errors"),
        ("ultimo_conversation_id", "messages_conversation_id"),
    ]
    for label, key in rows:
        if key in stats:
            table.add_row(label, str(stats.get(key)))
    elapsed = None
    if started_at:
        elapsed = str(datetime.now() - started_at).split(".", maxsplit=1)[0]
    return Group(
        _header_lines(width, "SYNC CONTACTOS", "MYSQL"),
        table,
        Text("-" * width, style="green"),
        _footer_line(width, elapsed=elapsed),
    )


def _compute_width(columns: list[tuple[str, int]]) -> int:
    return sum(width for _, width in columns) + (len(columns) - 1) * 3 + 4


def _clean_cell(value: str) -> str:
    cleaned = " ".join(value.replace("\t", " ").replace("\n", " ").split())
    return cleaned.encode("ascii", "ignore").decode("ascii")


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 3:
        return value[:width]
    return value[: max(0, width - 3)] + "..."


def _header_lines(width: int, title: str, source: str) -> Group:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = Text("=" * width, style="green")
    title_text = _fit_text(f"{title} | FUENTE: {source}", max(0, width - 20))
    header = Text(f"{title_text}".ljust(width - 20) + timestamp.rjust(20), style="green")
    return Group(line, header, line)


def _format_datetime_cell(key: str, raw: object) -> str:
    if raw is None:
        return ""
    if key in ("created_at", "last_activity_at"):
        try:
            ts = int(raw)
        except (TypeError, ValueError):
            return str(raw)
        dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=-3)))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(raw)


def _footer_line(width: int, *, elapsed: str | None = None) -> Text:
    if width < 60:
        footer = "F1=AYU  F3=SAL  F5=REF"
    elif width < 90:
        footer = "F1=AYUDA  F3=SALIR  F5=REFRESH  F8=SIG"
    else:
        footer = "F1=AYUDA  F3=SALIR  F5=REFRESH  F8=SIGUIENTE  F9=ANTERIOR"
    if elapsed:
        footer = f"{footer}  T={elapsed}"
    return Text(footer.ljust(width)[:width], style="yellow")


def _fit_text(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: max(0, width - 3)] + "..."


def _render_header(console: Console, width: int, title: str, source: str) -> None:
    console.print(_header_lines(width, title, source))


def _render_footer(console: Console, width: int, *, elapsed: str | None = None) -> None:
    console.print(Text("-" * width, style="green"))
    console.print(_footer_line(width, elapsed=elapsed))
