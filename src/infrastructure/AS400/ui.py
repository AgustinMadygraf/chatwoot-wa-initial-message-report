from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import floor
from shutil import get_terminal_size
import sys
from typing import Iterable

from rich import box
from rich.console import Console, Group
from rich.table import Table
from rich.text import Text


def print_inboxes_table(inboxes: Iterable[dict]) -> None:
    console = _console()
    columns = [
        ("id", 6),
        ("account_id", 10),
        ("name", 18),
        ("channel_type", 18),
        ("address", 20),
        ("last_synced_at", 19),
    ]
    _render_table_paginated(console, "INBOXES", "MYSQL", columns, inboxes, _row_from_raw)


def print_accounts_table(accounts: Iterable[dict]) -> None:
    console = _console()
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
    _render_table_paginated(console, "CUENTAS", "MYSQL", columns, accounts, _row_from_raw)


def print_conversations_table(conversations: Iterable[dict]) -> None:
    console = _console()
    columns = [
        ("id", 6),
        ("account_id", 10),
        ("inbox_id", 8),
        ("address", 20),
        ("created_at", 19),
        ("last_activity_at", 19),
        ("last_synced_at", 19),
    ]
    _render_table_paginated(
        console, "CONVERSACIONES", "MYSQL", columns, conversations, _row_from_raw
    )


def print_messages_table(messages: Iterable[dict]) -> None:
    console = _console()
    columns = [
        ("id", 7),
        ("conversation_id", 8),
        ("inbox_id", 8),
        ("created_at", 19),
        ("content", 28),
        ("last_synced_at", 19),
    ]
    _render_table_paginated(console, "MENSAJES", "MYSQL", columns, messages, _row_from_raw)


def print_health_screen(results: dict) -> None:
    console = _console()
    columns = [
        ("service", 10),
        ("status", 6),
        ("detail", 54),
    ]
    width = _screen_width()
    columns = _fit_columns(columns, width)
    _render_header(console, width, "ESTADO GENERAL", "CLI")
    table = _build_table(columns, width)
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
    started_at: datetime | None = None,
) -> None:
    console = _console()
    columns = [
        ("metric", 36),
        ("value", 37),
    ]
    width = _screen_width()
    columns = _fit_columns(columns, width)
    _render_header(console, width, "SYNC GENERAL", "MYSQL")
    table = _build_table(columns, width)
    table.columns[0].style = "green"
    table.columns[1].style = "bold green"
    for key, label in (
        ("accounts_upserted", "accounts_upserted"),
        ("inboxes_upserted", "inboxes_upserted"),
        ("conversations_upserted", "conversations_upserted"),
        ("messages_upserted", "messages_upserted"),
        ("messages_errors", "messages_errors"),
    ):
        if key in stats:
            table.add_row(label, str(stats.get(key)))
    console.print(table)
    elapsed = None
    if started_at:
        elapsed = str(datetime.now() - started_at).split(".", maxsplit=1)[0]
    _render_footer(console, width, elapsed=elapsed)


def build_sync_progress_screen(stats: dict, *, started_at: datetime | None = None) -> Group:
    console = _console()
    columns = [
        ("metric", 36),
        ("value", 37),
    ]
    width = _screen_width()
    columns = _fit_columns(columns, width)
    table = _build_table(columns, width)
    table.columns[0].style = "green"
    table.columns[1].style = "bold green"
    rows = [
        ("fase", "phase"),
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


def _render_table_paginated(
    console: Console,
    title: str,
    source: str,
    columns: list[tuple[str, int]],
    rows: Iterable[dict],
    row_builder,
) -> None:
    width = _screen_width()
    columns = _fit_columns(columns, width)
    rows = list(rows)
    if not _is_tty():
        _render_table_once(console, width, title, source, columns, rows, row_builder)
        return
    page_size = _page_size()
    page = 0
    total_pages = max(1, (len(rows) + page_size - 1) // page_size)
    while True:
        start = page * page_size
        end = start + page_size
        page_rows = rows[start:end]
        _render_table_once(
            console, width, title, source, columns, page_rows, row_builder, page, total_pages
        )
        key = _read_key()
        if key in {"F3", "ESC", "Q"}:
            break
        if key in {"F8", "RIGHT", "N"} and page < total_pages - 1:
            page += 1
            continue
        if key in {"F9", "LEFT", "P"} and page > 0:
            page -= 1
            continue
        if key == "F5":
            continue


def _render_table_once(
    console: Console,
    width: int,
    title: str,
    source: str,
    columns: list[tuple[str, int]],
    rows: Iterable[dict],
    row_builder,
    page: int | None = None,
    total_pages: int | None = None,
) -> None:
    _render_header(console, width, title, source)
    table = _build_table(columns, width)
    for col in table.columns:
        col.style = "green"
    table.columns[0].style = "bold green"
    for row in rows:
        table.add_row(*row_builder(row, columns))
    console.print(table)
    page_info = None
    if page is not None and total_pages is not None:
        page_info = f"P={page + 1}/{total_pages}"
    _render_footer(console, width, page_info=page_info)


def _build_table(columns: list[tuple[str, int]], width: int) -> Table:
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold yellow",
        row_styles=["", ""],
        width=width,
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
    return table


def _row_from_raw(item: dict, columns: list[tuple[str, int]]) -> list[str]:
    row = []
    for key, col_width in columns:
        raw = item.get(key)
        value = _format_datetime_cell(key, raw)
        value = _clean_cell(value)
        row.append(_truncate(value, col_width))
    return row


def _screen_width() -> int:
    return max(40, _terminal_size().columns)


def _page_size() -> int:
    return max(5, _terminal_size().lines - 8)


def _fit_columns(columns: list[tuple[str, int]], width: int) -> list[tuple[str, int]]:
    gaps = (len(columns) - 1) * 3 + 4
    available = max(20, width - gaps)
    total = sum(col_width for _, col_width in columns)
    if total <= available:
        return columns
    ratio = available / total
    resized = []
    for label, col_width in columns:
        resized.append((label, max(4, floor(col_width * ratio))))
    diff = available - sum(col_width for _, col_width in resized)
    if diff > 0:
        last_label, last_width = resized[-1]
        resized[-1] = (last_label, last_width + diff)
    return resized


def _is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _terminal_size():
    try:
        return get_terminal_size(fallback=(80, 24))
    except Exception:
        return get_terminal_size(fallback=(80, 24))


def _console() -> Console:
    size = _terminal_size()
    return Console(width=size.columns, height=size.lines)


def _read_key() -> str:
    try:
        import msvcrt

        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            code = ord(msvcrt.getwch())
            return {
                61: "F3",
                63: "F5",
                66: "F8",
                67: "F9",
                75: "LEFT",
                77: "RIGHT",
            }.get(code, "")
        if ch in ("\x1b", "q", "Q"):
            return "Q"
        if ch in ("8", "n", "N"):
            return "N"
        if ch in ("9", "p", "P"):
            return "P"
        return ch
    except Exception:
        try:
            ch = input().strip().lower()
        except Exception:
            return ""
        return ch[:1].upper() if ch else ""


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
        if isinstance(raw, (int, str)):
            try:
                ts = int(raw)
            except ValueError:
                return str(raw)
            dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=-3)))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return str(raw)
    return str(raw)


def _footer_line(
    width: int,
    *,
    elapsed: str | None = None,
    page_info: str | None = None,
) -> Text:
    if width < 60:
        footer = "F1=AYU  F3=SAL  F5=REF  F8=SIG  F9=ANT"
    elif width < 90:
        footer = "F1=AYUDA  F3=SALIR  F5=REFRESH  F8=SIG  F9=ANT"
    else:
        footer = "F1=AYUDA  F3=SALIR  F5=REFRESH  F8=SIGUIENTE  F9=ANTERIOR"
    if page_info:
        footer = f"{footer}  {page_info}"
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


def _render_footer(
    console: Console,
    width: int,
    *,
    elapsed: str | None = None,
    page_info: str | None = None,
) -> None:
    console.print(Text("-" * width, style="green"))
    console.print(_footer_line(width, elapsed=elapsed, page_info=page_info))
