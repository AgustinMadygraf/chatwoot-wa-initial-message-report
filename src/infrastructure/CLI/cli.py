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
from src.infrastructure.CLI.ui import (
    build_sync_progress_screen,
    print_accounts_table,
    print_conversations_table,
    print_health_screen,
    print_inboxes_table,
    print_messages_table,
    print_sync_screen,
)
from src.infrastructure.pymysql.accounts_repository import AccountsRepository
from src.infrastructure.pymysql.connection import get_mysql_connection
from src.infrastructure.pymysql.conversations_repository import ConversationsRepository
from src.infrastructure.pymysql.inboxes_repository import InboxesRepository
from src.infrastructure.pymysql.messages_repository import MessagesRepository
from src.shared.config import get_env, load_env_file
from src.shared.logger import get_logger
from src.use_cases.accounts_sync import sync_account
from src.use_cases.conversations_sync import sync_conversations
from src.use_cases.health_check import run_health_checks
from src.use_cases.inboxes_sync import sync_inboxes
from src.use_cases.messages_sync import sync_messages


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica conectividad con Chatwoot API y MySQL.")
    parser.add_argument("--json", action="store_true", help="Imprime salida en JSON.")
    parser.add_argument("--debug", action="store_true", help="Habilita logs de depuración.")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Sincroniza cuentas, inboxes, conversaciones y mensajes.",
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

    if (
        sum(
            [
                bool(args.sync),
                bool(args.list_accounts),
                bool(args.list_inboxes),
                bool(args.list_conversations),
                bool(args.list_messages),
            ]
        )
        > 1
    ):
        print(
            "Error: usa solo una opcion: --sync, --list-inboxes, --list-accounts, "
            "--list-conversations o --list-messages."
        )
        sys.exit(1)

    if args.list_inboxes:
        try:
            mysql_config = MySQLConfig(
                host=_require_env("MYSQL_HOST"),
                user=_require_env("MYSQL_USER"),
                password=_require_env("MYSQL_PASSWORD"),
                database=_require_env("MYSQL_DB"),
                port=int(get_env("MYSQL_PORT", "3306")),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Listar inboxes fallo: {exc}")
            sys.exit(1)

        conn = get_mysql_connection(mysql_config)
        repo = InboxesRepository(conn, account_id=int(_require_env("CHATWOOT_ACCOUNT_ID")))
        try:
            repo.ensure_table()
            inboxes = repo.list_inboxes()
            print_inboxes_table(inboxes)
        finally:
            conn.close()
        return

    if args.list_conversations:
        try:
            mysql_config = MySQLConfig(
                host=_require_env("MYSQL_HOST"),
                user=_require_env("MYSQL_USER"),
                password=_require_env("MYSQL_PASSWORD"),
                database=_require_env("MYSQL_DB"),
                port=int(get_env("MYSQL_PORT", "3306")),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Listar conversaciones fallo: {exc}")
            sys.exit(1)

        conn = get_mysql_connection(mysql_config)
        repo = ConversationsRepository(conn)
        try:
            repo.ensure_table()
            conversations = repo.list_conversations()
            print_conversations_table(conversations)
        finally:
            conn.close()
        return

    if args.list_messages:
        try:
            mysql_config = MySQLConfig(
                host=_require_env("MYSQL_HOST"),
                user=_require_env("MYSQL_USER"),
                password=_require_env("MYSQL_PASSWORD"),
                database=_require_env("MYSQL_DB"),
                port=int(get_env("MYSQL_PORT", "3306")),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Listar mensajes fallo: {exc}")
            sys.exit(1)

        conn = get_mysql_connection(mysql_config)
        repo = MessagesRepository(conn)
        try:
            repo.ensure_table()
            messages = repo.list_messages()
            print_messages_table(messages)
        finally:
            conn.close()
        return

    if args.list_accounts:
        try:
            mysql_config = MySQLConfig(
                host=_require_env("MYSQL_HOST"),
                user=_require_env("MYSQL_USER"),
                password=_require_env("MYSQL_PASSWORD"),
                database=_require_env("MYSQL_DB"),
                port=int(get_env("MYSQL_PORT", "3306")),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Listar cuentas fallo: {exc}")
            sys.exit(1)

        conn = get_mysql_connection(mysql_config)
        repo = AccountsRepository(conn)
        try:
            repo.ensure_table()
            accounts = repo.list_accounts()
            print_accounts_table(accounts)
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
            print(f"Sync fallo: {exc}")
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
        accounts_repo = AccountsRepository(conn)
        inboxes_repo = InboxesRepository(conn, account_id=int(_require_env("CHATWOOT_ACCOUNT_ID")))
        conversations_repo = ConversationsRepository(conn)
        messages_repo = MessagesRepository(conn)
        started_at = datetime.now()
        progress_logger = logger if args.debug else get_logger("cli", level="WARNING")

        sync_stats = {"phase": "accounts"}

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
                print("\\nSync cancelado por el usuario.")
            except Exception as exc:  # noqa: BLE001
                sync_stats["phase"] = "error"
                _update_live()
                print(f"\nSync fallo: {exc}")
        conn.close()
        print_sync_screen(sync_stats, started_at=started_at)
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
