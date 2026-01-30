"""
Path: src/infrastructure/CLI/cli.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from entities.mysql_config import MySQLConfig
from infrastructure.chatwoot_api.client import ChatwootClient, ChatwootClientConfig
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

import infrastructure.AS400.cli as as400_cli


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


def _handle_sync_plain(args, logger) -> None:
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

    print("Inicio sync:", started_at.isoformat(timespec="seconds"))
    with PyMySQLUnitOfWork(mysql_config) as uow:
        accounts_repo = AccountsRepository(uow.connection)
        inboxes_repo = InboxesRepository(
            uow.connection, account_id=int(_require_env("CHATWOOT_ACCOUNT_ID"))
        )
        conversations_repo = ConversationsRepository(uow.connection)
        messages_repo = MessagesRepository(uow.connection)

        try:
            print("Sync cuentas...")
            accounts_result = sync_account(client, accounts_repo, logger=progress_logger)
            print("Cuentas upserted:", accounts_result.get("total_upserted", 0))

            print("Sync inboxes...")
            inboxes_result = sync_inboxes(client, inboxes_repo, logger=progress_logger)
            print("Inboxes upserted:", inboxes_result.get("total_upserted", 0))

            print("Sync conversaciones...")

            def _convo_progress(page: int, total: int) -> None:
                print(f"Conversaciones pagina {page} -> total {total}")

            conversation_ids = sync_conversations(
                client,
                conversations_repo,
                logger=progress_logger,
                per_page=args.per_page,
                progress=_convo_progress,
            )

            print("Sync mensajes...")

            def _msg_progress(conversation_id: int, total: int, errors: int) -> None:
                print(
                    f"Mensajes conv {conversation_id} -> total {total} (errores {errors})"
                )

            sync_messages(
                client,
                messages_repo,
                conversation_ids,
                logger=progress_logger,
                per_page=args.per_page,
                progress=_msg_progress,
            )
        except KeyboardInterrupt:
            print("Sync cancelado por el usuario.")
            return
        except (ValueError, RuntimeError):
            raise
    finished_at = datetime.now()
    print("Fin sync:", finished_at.isoformat(timespec="seconds"))
    print("Duracion:", finished_at - started_at)

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

    print("Inicio sync mensajes:", started_at.isoformat(timespec="seconds"))
    with PyMySQLUnitOfWork(mysql_config) as uow:
        conversations_repo = ConversationsRepository(uow.connection)
        messages_repo = MessagesRepository(uow.connection)
        conversations_repo.ensure_table()
        messages_repo.ensure_table()
        rows = conversations_repo.list_conversations()
        conversation_ids = [int(row["id"]) for row in rows if row.get("id") is not None]
        if not conversation_ids:
            print("No hay conversaciones en MySQL. Ejecuta --sync primero.")
            return

        def _msg_progress(conversation_id: int, total: int, errors: int) -> None:
            print(
                f"Mensajes conv {conversation_id} -> total {total} (errores {errors})"
            )

        sync_messages(
            client,
            messages_repo,
            conversation_ids,
            logger=progress_logger,
            per_page=args.per_page,
            progress=_msg_progress,
        )
    finished_at = datetime.now()
    print("Fin sync mensajes:", finished_at.isoformat(timespec="seconds"))
    print("Duracion:", finished_at - started_at)

def main() -> None:
    "Punto de entrada para la aplicacion CLI."
    load_env_file()
    if len(sys.argv) == 1:
        as400_cli.main()
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
            as400_cli._handle_list_inboxes()
        except (ValueError, RuntimeError) as exc:
            print(f"Listar inboxes fallo: {exc}")
            sys.exit(1)
        return

    if args.list_conversations:
        try:
            as400_cli._handle_list_conversations()
        except (ValueError, RuntimeError) as exc:
            print(f"Listar conversaciones fallo: {exc}")
            sys.exit(1)
        return

    if args.list_messages:
        try:
            as400_cli._handle_list_messages()
        except (ValueError, RuntimeError) as exc:
            print(f"Listar mensajes fallo: {exc}")
            sys.exit(1)
        return

    if args.list_accounts:
        try:
            as400_cli._handle_list_accounts()
        except (ValueError, RuntimeError) as exc:
            print(f"Listar cuentas fallo: {exc}")
            sys.exit(1)
        return

    if args.sync:
        try:
            _handle_sync_plain(args, logger)
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
