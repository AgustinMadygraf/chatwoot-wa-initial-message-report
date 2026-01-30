"""
Path: src/infrastructure/AS400/cli.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import cast

from rich.live import Live
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

from entities.mysql_config import MySQLConfig
from infrastructure.chatwoot_api.client import ChatwootClient, ChatwootClientConfig
from infrastructure.AS400.ui import (
    build_sync_progress_screen,
    print_accounts_table,
    print_conversations_table,
    print_health_screen,
    print_inboxes_table,
    print_messages_table,
    print_sync_screen,
)
from infrastructure.pymysql.accounts_repository import AccountsRepository
from infrastructure.pymysql.conversations_repository import ConversationsRepository
from infrastructure.pymysql.fetchers import (
    fetch_accounts,
    fetch_conversations,
    fetch_inboxes,
    fetch_messages,
)
from infrastructure.pymysql.inboxes_repository import InboxesRepository
from infrastructure.pymysql.messages_repository import MessagesRepository
from infrastructure.pymysql.unit_of_work import PyMySQLUnitOfWork
from infrastructure.health_check import EnvironmentHealthCheck
from infrastructure.AS400.tui.app import As400App
from shared.config import get_env, load_env_file
from shared.logger import get_logger
from application.use_cases.accounts_sync import sync_account
from application.use_cases.conversations_sync import sync_conversations
from application.use_cases.health_check import run_health_checks
from application.ports.health_check import HealthCheckResults, HealthServiceStatus
from application.use_cases.inboxes_sync import sync_inboxes
from application.use_cases.messages_sync import sync_messages




def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica conectividad con Chatwoot API y MySQL.")
    parser.add_argument("--json", action="store_true", help="Imprime salida en JSON.")
    parser.add_argument("--debug", action="store_true", help="Habilita logs de depuracion.")
    parser.add_argument("--tui", action="store_true", help="Inicia la interfaz AS/400 en Textual.")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Sincroniza cuentas, inboxes, conversaciones y mensajes.",
    )
    parser.add_argument(
        "--sync-messages",
        action="store_true",
        help="Sincroniza solo mensajes usando conversaciones ya guardadas en MySQL.",
    )
    parser.add_argument(
        "--list-inboxes",
        action="store_true",
        help="Lista inboxes desde MySQL.",
    )
    parser.add_argument(
        "--list-accounts",
        action="store_true",
        help="Lista detalles de la cuenta desde MySQL.",
    )
    parser.add_argument(
        "--list-conversations",
        action="store_true",
        help="Lista conversaciones desde MySQL.",
    )
    parser.add_argument(
        "--list-messages",
        action="store_true",
        help="Lista mensajes desde MySQL.",
    )
    parser.add_argument("--per-page", type=int, default=None)
    return parser.parse_args()


def _require_env(name: str) -> str:
    value = get_env(name)
    if value is None or value == "":
        raise ValueError(f"Missing env var: {name}")
    return str(value)


def _show_menu() -> str:
    console = Console()
    console.print()
    table = Table(
        box=box.SIMPLE,
        show_lines=False,
        title="MENU PRINCIPAL (AS/400)",
        title_style="bold green",
        width=min(80, console.size.width - 4),
    )
    table.add_column("OPCION", justify="right", width=8, style="bold cyan")
    table.add_column("DESCRIPCION", style="green")
    table.add_row("1", "Estado general / health check")
    table.add_row("2", "Listar cuentas")
    table.add_row("3", "Listar inboxes")
    table.add_row("4", "Listar conversaciones")
    table.add_row("5", "Listar mensajes")
    table.add_row("6", "Sincronizar todo")
    table.add_row("0", "Salir")
    console.print(table)
    console.print(Text("Seleccion: ", style="bold yellow"), end="")
    return input().strip()


def _handle_health(logger) -> None:
    checker = EnvironmentHealthCheck(logger=logger)
    results = cast(HealthCheckResults, run_health_checks(checker, logger=logger))
    print_health_screen(results)


def _handle_list_inboxes() -> None:
    inboxes = fetch_inboxes(int(_require_env("CHATWOOT_ACCOUNT_ID")))
    print_inboxes_table(inboxes)


def _handle_list_conversations() -> None:
    conversations = fetch_conversations()
    print_conversations_table(conversations)


def _handle_list_messages() -> None:
    messages = fetch_messages()
    print_messages_table(messages)


def _handle_list_accounts() -> None:
    accounts = fetch_accounts()
    print_accounts_table(accounts)


def _handle_sync(args, logger) -> None:
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
    client = ChatwootClient(chatwoot_config, logger=logger if args.debug else None)
    started_at = datetime.now()
    progress_logger = logger if args.debug else get_logger("cli", level="WARNING")
    sync_stats: dict[str, object] = {"phase": "accounts"}

    with PyMySQLUnitOfWork(mysql_config) as uow:
        accounts_repo = AccountsRepository(uow.connection)
        inboxes_repo = InboxesRepository(
            uow.connection, account_id=int(_require_env("CHATWOOT_ACCOUNT_ID"))
        )
        conversations_repo = ConversationsRepository(uow.connection)
        messages_repo = MessagesRepository(uow.connection)

        def _update_live() -> None:
            live.update(build_sync_progress_screen(sync_stats, started_at=started_at))

        with Live(
            build_sync_progress_screen(sync_stats, started_at=started_at),
            refresh_per_second=4,
        ) as live:
            try:
                sync_stats["accounts_upserted"] = sync_account(
                    client, accounts_repo, logger=progress_logger
                ).get("total_upserted", 0)
                _update_live()
                sync_stats["phase"] = "inboxes"
                _update_live()
                sync_stats["inboxes_upserted"] = sync_inboxes(
                    client, inboxes_repo, logger=progress_logger
                ).get("total_upserted", 0)
                _update_live()
                sync_stats["phase"] = "conversaciones"
                _update_live()

                def _convo_progress(page: int, total: int) -> None:
                    sync_stats["conversations_page"] = page
                    sync_stats["conversations_upserted"] = total
                    _update_live()

                conversation_ids = sync_conversations(
                    client,
                    conversations_repo,
                    logger=progress_logger,
                    per_page=args.per_page,
                    progress=_convo_progress,
                )
                sync_stats["phase"] = "mensajes"
                _update_live()

                def _msg_progress(conversation_id: int, total: int, errors: int) -> None:
                    sync_stats["messages_conversation_id"] = conversation_id
                    sync_stats["messages_upserted"] = total
                    sync_stats["messages_errors"] = errors
                    _update_live()

                sync_messages(
                    client,
                    messages_repo,
                    conversation_ids,
                    logger=progress_logger,
                    per_page=args.per_page,
                    progress=_msg_progress,
                )
            except KeyboardInterrupt:
                sync_stats["phase"] = "cancelado"
                _update_live()
                print("\nSync cancelado por el usuario.")
            except (ValueError, RuntimeError) as exc:
                sync_stats["phase"] = "error"
                _update_live()
                print(f"\nSync fallo: {exc}")
    print_sync_screen(sync_stats, started_at=started_at)

def _handle_sync_messages_only(args, logger) -> None:
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
    client = ChatwootClient(chatwoot_config, logger=logger if args.debug else None)
    started_at = datetime.now()
    progress_logger = logger if args.debug else get_logger("cli", level="WARNING")
    sync_stats: dict[str, object] = {"phase": "mensajes"}

    with PyMySQLUnitOfWork(mysql_config) as uow:
        conversations_repo = ConversationsRepository(uow.connection)
        messages_repo = MessagesRepository(uow.connection)
        conversations_repo.ensure_table()
        messages_repo.ensure_table()
        rows = conversations_repo.list_conversations()
        rows = sorted(
            rows,
            key=lambda row: (
                int(row.get("account_id") or 0),
                int(row.get("inbox_id") or 0),
                int(row.get("id") or 0),
            ),
        )
        conversation_ids = [int(row["id"]) for row in rows if row.get("id") is not None]
        if not conversation_ids:
            sync_stats["phase"] = "sin_conversaciones"
            print_sync_screen(sync_stats, started_at=started_at)
            print("No hay conversaciones en MySQL. Ejecuta --sync primero.")
            return

        def _msg_progress(conversation_id: int, total: int, errors: int) -> None:
            # Commit per page so partial progress is persisted on long runs.
            uow.commit()
            sync_stats["messages_conversation_id"] = conversation_id
            sync_stats["messages_upserted"] = total
            sync_stats["messages_errors"] = errors
            print_sync_screen(sync_stats, started_at=started_at)

        try:
            sync_messages(
                client,
                messages_repo,
                conversation_ids,
                logger=progress_logger,
                per_page=args.per_page,
                progress=_msg_progress,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"sync_messages error: {type(exc).__name__}: {exc!r}") from exc
    print_sync_screen(sync_stats, started_at=started_at)


def main() -> None:
    "Punto de entrada para la aplicacion CLI."
    load_env_file()
    if len(sys.argv) == 1:
        logger = get_logger("cli", level="INFO")
        while True:
            choice = _show_menu()
            if choice == "0":
                return
            try:
                if choice == "1":
                    _handle_health(logger)
                elif choice == "2":
                    _handle_list_accounts()
                elif choice == "3":
                    _handle_list_inboxes()
                elif choice == "4":
                    _handle_list_conversations()
                elif choice == "5":
                    _handle_list_messages()
                elif choice == "6":
                    args = argparse.Namespace(debug=False, per_page=None)
                    _handle_sync(args, logger)
                else:
                    print("Opcion invalida.")
            except (ValueError, RuntimeError, KeyboardInterrupt) as exc:
                print(f"Error: {exc}")
        return

    args = _get_args()
    logger = get_logger("cli", level="DEBUG" if args.debug else "INFO")

    if (
        sum(
            [
                bool(args.sync),
                bool(args.sync_messages),
                bool(args.list_accounts),
                bool(args.list_inboxes),
                bool(args.list_conversations),
                bool(args.list_messages),
            ]
        )
        > 1
    ):
        print(
            "Error: usa solo una opcion: --sync, --sync-messages, --list-inboxes, "
            "--list-accounts, --list-conversations o --list-messages."
        )
        sys.exit(1)

    if args.tui:
        As400App().run()
        return

    if args.list_inboxes:
        try:
            _handle_list_inboxes()
        except (ValueError, RuntimeError) as exc:
            print(f"Listar inboxes fallo: {exc}")
            sys.exit(1)
        return

    if args.list_conversations:
        try:
            _handle_list_conversations()
        except (ValueError, RuntimeError) as exc:
            print(f"Listar conversaciones fallo: {exc}")
            sys.exit(1)
        return

    if args.list_messages:
        try:
            _handle_list_messages()
        except (ValueError, RuntimeError) as exc:
            print(f"Listar mensajes fallo: {exc}")
            sys.exit(1)
        return

    if args.list_accounts:
        try:
            _handle_list_accounts()
        except (ValueError, RuntimeError) as exc:
            print(f"Listar cuentas fallo: {exc}")
            sys.exit(1)
        return

    if args.sync:
        try:
            _handle_sync(args, logger)
        except (ValueError, RuntimeError, KeyboardInterrupt) as exc:
            print(f"Sync fallo: {exc}")
            sys.exit(1)
        return
    if args.sync_messages:
        try:
            _handle_sync_messages_only(args, logger)
        except (ValueError, RuntimeError, KeyboardInterrupt) as exc:
            print(f"Sync mensajes fallo: {exc}")
            sys.exit(1)
        return

    checker = EnvironmentHealthCheck(logger=logger)
    results = run_health_checks(checker, logger=logger)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    print("Estado general:", "OK" if results["ok"] else "ERROR")
    for key in ("chatwoot", "mysql"):
        item: HealthServiceStatus = results[key]
        status = "OK" if item["ok"] else "ERROR"
        detail = f" - {item.get('error')}" if item.get("error") else ""
        print(f"{key}: {status}{detail}")
