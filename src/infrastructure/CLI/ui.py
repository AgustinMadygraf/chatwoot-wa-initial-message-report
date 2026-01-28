from __future__ import annotations

from datetime import datetime

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
            ("name", 17),
            ("phone_number", 12),
            ("email", 21),
            ("updated_at", 8),
        ]
    width = SCREEN_WIDTH
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
            value = "" if raw is None else str(raw)
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


def build_sync_progress_screen(page: int, stats: dict, *, started_at: datetime | None = None) -> Group:
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
    table.add_row("pagina", str(page))
    table.add_row("listados", str(stats.get("total_listed", 0)))
    table.add_row("upserted", str(stats.get("total_upserted", 0)))
    table.add_row("skipped", str(stats.get("total_skipped", 0)))
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
