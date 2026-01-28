from __future__ import annotations

import argparse
import json
import sys

from datetime import datetime

from rich import box
from rich.console import Console
from rich.table import Table

from src.entities.mysql_config import MySQLConfig
from src.infrastructure.chatwoot_api.client import ChatwootClient, ChatwootClientConfig
from src.infrastructure.pymysql.connection import get_mysql_connection
from src.infrastructure.pymysql.contacts_repository import ContactsRepository
from src.shared.config import get_env, load_env_file
from src.shared.logger import get_logger
from src.use_cases.contacts_list import list_contacts_with_first_message
from src.use_cases.contacts_sync import sync_contacts
from src.use_cases.health_check import run_health_checks


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica conectividad con Chatwoot API y MySQL.")
    parser.add_argument("--json", action="store_true", help="Imprime salida en JSON.")
    parser.add_argument("--debug", action="store_true", help="Habilita logs de depuración.")
    parser.add_argument("--sync-contacts", action="store_true", help="Descarga contactos a MySQL.")
    parser.add_argument("--list-contacts", action="store_true", help="Lista contactos desde MySQL.")
    parser.add_argument(
        "--list-contacts-with-first-message",
        action="store_true",
        help="Lista contactos y su primer mensaje entrante (puede ser lento).",
    )
    parser.add_argument("--contacts-per-page", type=int, default=None)
    return parser.parse_args()


def _require_env(name: str) -> str:
    value = get_env(name)
    if not value:
        raise ValueError(f"Missing env var: {name}")
    return value


def main() -> None:
    load_env_file()
    if len(sys.argv) == 1:
        logger = get_logger("cli", level="INFO")
        results = run_health_checks(logger=logger)
        print("Estado general:", "OK" if results["ok"] else "ERROR")
        for key in ("chatwoot", "mysql"):
            item = results[key]
            status = "OK" if item["ok"] else "ERROR"
            detail = f" - {item.get('error')}" if item.get("error") else ""
            print(f"{key}: {status}{detail}")
        return

    args = _get_args()
    logger = get_logger("cli", level="DEBUG" if args.debug else "INFO")

    if sum(
        [
            bool(args.sync_contacts),
            bool(args.list_contacts),
            bool(args.list_contacts_with_first_message),
        ]
    ) > 1:
        print(
            "Error: usa solo una opcion: --sync-contacts, --list-contacts o "
            "--list-contacts-with-first-message."
        )
        sys.exit(1)

    if args.list_contacts_with_first_message:
        try:
            chatwoot_config = ChatwootClientConfig(
                base_url=_require_env("CHATWOOT_BASE_URL"),
                account_id=_require_env("CHATWOOT_ACCOUNT_ID"),
                api_token=_require_env("CHATWOOT_API_ACCESS_TOKEN"),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Listar contactos fallo: {exc}")
            sys.exit(1)

        client = ChatwootClient(chatwoot_config, logger=logger if args.debug else None)
        _print_contacts_table(
            list_contacts_with_first_message(
                client, logger=logger, per_page=args.contacts_per_page
            ),
            include_first_message=True,
        )
        return

    if args.list_contacts:
        try:
            mysql_config = MySQLConfig(
                host=_require_env("MYSQL_HOST"),
                user=_require_env("MYSQL_USER"),
                password=_require_env("MYSQL_PASSWORD"),
                database=_require_env("MYSQL_DB"),
                port=int(get_env("MYSQL_PORT", "3306")),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Listar contactos fallo: {exc}")
            sys.exit(1)

        conn = get_mysql_connection(mysql_config)
        repo = ContactsRepository(conn)
        try:
            _print_contacts_table(repo.list_contacts())
        finally:
            conn.close()
        return

    if args.sync_contacts:
        try:
            chatwoot_config = ChatwootClientConfig(
                base_url=_require_env("CHATWOOT_BASE_URL"),
                account_id=_require_env("CHATWOOT_ACCOUNT_ID"),
                api_token=_require_env("CHATWOOT_API_ACCESS_TOKEN"),
            )
            mysql_config = MySQLConfig(
                host=_require_env("MYSQL_HOST"),
                user=_require_env("MYSQL_USER"),
                password=_require_env("MYSQL_PASSWORD"),
                database=_require_env("MYSQL_DB"),
                port=int(get_env("MYSQL_PORT", "3306")),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Sync contactos fallo: {exc}")
            sys.exit(1)

        client = ChatwootClient(chatwoot_config, logger=logger if args.debug else None)
        try:
            conn = get_mysql_connection(mysql_config)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "No se pudo conectar a MySQL. Verifica MYSQL_HOST, MYSQL_USER, "
                "MYSQL_PASSWORD, MYSQL_DB y MYSQL_PORT."
            )
            raise SystemExit("Fallo la conexion a MySQL.") from exc
        repo = ContactsRepository(conn)
        stats = sync_contacts(client, repo, logger=logger, per_page=args.contacts_per_page)
        conn.close()
        logger.info(
            "Sync contactos OK. "
            f"listados={stats.get('total_listed')} "
            f"upserted={stats.get('total_upserted')} "
            f"skipped={stats.get('total_skipped')}"
        )
        return

    results = run_health_checks(logger=logger)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    print("Estado general:", "OK" if results["ok"] else "ERROR")
    for key in ("chatwoot", "mysql"):
        item = results[key]
        status = "OK" if item["ok"] else "ERROR"
        detail = f" - {item.get('error')}" if item.get("error") else ""
        print(f"{key}: {status}{detail}")


def _clean_cell(value: str) -> str:
    cleaned = " ".join(value.replace("\t", " ").replace("\n", " ").split())
    return cleaned.encode("ascii", "ignore").decode("ascii")


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 3:
        return value[:width]
    return value[: max(0, width - 3)] + "..."


def _print_contacts_table(contacts, include_first_message: bool = False) -> None:
    console = Console()
    columns = [
        ("id", 10),
        ("name", 30),
        ("phone_number", 18),
        ("email", 30),
        ("identifier", 20),
        ("updated_at", 12),
    ]
    if include_first_message:
        columns.append(("first_message", 40))
    width = sum(width for _, width in columns) + (len(columns) - 1) * 3 + 4
    _render_header(
        console,
        width,
        "LISTADO CONTACTOS",
        "CHATWOOT API" if include_first_message else "MYSQL",
    )
    table = Table(
        box=box.ASCII,
        show_header=True,
        header_style="bold cyan",
        row_styles=["", "dim"],
    )
    for label, width in columns:
        table.add_column(
            label,
            width=width,
            min_width=width,
            max_width=width,
            overflow="ellipsis",
            no_wrap=True,
            style="white",
        )
    table.columns[0].style = "bold green"
    table.columns[1].style = "bright_white"
    table.columns[2].style = "yellow"
    table.columns[3].style = "magenta"
    table.columns[4].style = "blue"
    table.columns[5].style = "bright_black"
    if include_first_message:
        table.columns[6].style = "cyan"
    for contact in contacts:
        row = []
        for key, width in columns:
            raw = contact.get(key)
            value = "" if raw is None else str(raw)
            value = _clean_cell(value)
            row.append(_truncate(value, width))
        table.add_row(*row)
    console.print(table)
    _render_footer(console, width)


def _render_header(console: Console, width: int, title: str, source: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "=" * width
    console.print(line, style="green")
    title_text = f"{title} | FUENTE: {source}"
    if len(title_text) > width - 20:
        title_text = title_text[: width - 23] + "..."
    header = f"{title_text}".ljust(width - 20) + timestamp.rjust(20)
    console.print(header, style="green")
    console.print(line, style="green")


def _render_footer(console: Console, width: int) -> None:
    line = "-" * width
    console.print(line, style="green")
    footer = "F1=AYUDA  F3=SALIR  F5=REFRESH  F8=SIGUIENTE  F9=ANTERIOR"
    console.print(footer.ljust(width)[:width], style="yellow")
