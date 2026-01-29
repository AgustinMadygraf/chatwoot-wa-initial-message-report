"""
Path: src/infrastructure/CLI/cli.py
"""

from __future__ import annotations

import argparse
import json
import sys

from datetime import datetime

from rich.live import Live

from src.entities.mysql_config import MySQLConfig
from src.infrastructure.chatwoot_api.client import ChatwootClient, ChatwootClientConfig
from src.infrastructure.pymysql.connection import get_mysql_connection
from src.infrastructure.pymysql.contacts_repository import ContactsRepository
from src.shared.config import get_env, load_env_file
from src.shared.logger import get_logger
from src.use_cases.contacts_list import list_contacts_with_first_message
from src.use_cases.contacts_sync import sync_contacts
from src.use_cases.health_check import run_health_checks
from src.infrastructure.CLI.ui import (
    build_sync_progress_screen,
    print_channels_table,
    print_contacts_by_channel_table,
    print_contacts_table,
    print_health_screen,
    print_sync_screen,
)


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica conectividad con Chatwoot API y MySQL.")
    parser.add_argument("--json", action="store_true", help="Imprime salida en JSON.")
    parser.add_argument("--debug", action="store_true", help="Habilita logs de depuración.")
    parser.add_argument("--sync", action="store_true", help="Descarga contactos a MySQL.")
    parser.add_argument(
        "--list-contacts",
        action="store_true",
        help="Lista contactos desde MySQL (incluye canales; filtros opcionales).",
    )
    parser.add_argument(
        "--list-channel",
        action="store_true",
        help="Lista canales/inboxes desde MySQL.",
    )
    parser.add_argument("--inbox-id", type=int, default=None)
    parser.add_argument("--provider", type=str, default=None)
    parser.add_argument("--channel-type", type=str, default=None)
    parser.add_argument("--inbox-name", type=str, default=None)
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
        print_health_screen(results)
        return

    args = _get_args()
    logger = get_logger("cli", level="DEBUG" if args.debug else "INFO")

    if sum(
        [
            bool(args.sync),
            bool(args.list_contacts),
            bool(args.list_channel),
            bool(args.list_contacts_with_first_message),
        ]
    ) > 1:
        print(
            "Error: usa solo una opcion: --sync, --list-contacts, --list-channel o "
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
        print_contacts_table(
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
            print(f"Listar contactos por canal fallo: {exc}")
            sys.exit(1)

        conn = get_mysql_connection(mysql_config)
        repo = ContactsRepository(conn)
        try:
            repo.ensure_table()
            contacts = repo.list_contacts_by_channel(
                inbox_id=args.inbox_id,
                provider=args.provider,
                channel_type=args.channel_type,
                inbox_name=args.inbox_name,
            )
            print_contacts_by_channel_table(contacts)
        finally:
            conn.close()
        return

    if args.list_channel:
        try:
            mysql_config = MySQLConfig(
                host=_require_env("MYSQL_HOST"),
                user=_require_env("MYSQL_USER"),
                password=_require_env("MYSQL_PASSWORD"),
                database=_require_env("MYSQL_DB"),
                port=int(get_env("MYSQL_PORT", "3306")),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Listar canales fallo: {exc}")
            sys.exit(1)

        conn = get_mysql_connection(mysql_config)
        repo = ContactsRepository(conn)
        try:
            repo.ensure_table()
            channels = repo.list_channels()
            print_channels_table(channels)
        finally:
            conn.close()
        return

    if args.sync:
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
        started_at = datetime.now()
        progress_logger = logger if args.debug else get_logger("cli", level="WARNING")

        def _progress(page: int, current_stats: dict) -> None:
            live.update(
                build_sync_progress_screen(page, current_stats, started_at=started_at)
            )

        with Live(
            build_sync_progress_screen(
                0,
                {"total_listed": 0, "total_upserted": 0, "total_skipped": 0},
                started_at=started_at,
            ),
            refresh_per_second=4,
        ) as live:
            stats = sync_contacts(
                client,
                repo,
                logger=progress_logger,
                per_page=args.contacts_per_page,
                progress=_progress,
            )
        total_in_db = repo.count_contacts()
        conn.close()
        print_sync_screen(stats, total_in_db=total_in_db, started_at=started_at)
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
