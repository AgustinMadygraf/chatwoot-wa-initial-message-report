from __future__ import annotations

import argparse
import json
import sys

from src.entities.mysql_config import MySQLConfig
from src.infrastructure.chatwoot_api.client import ChatwootClient, ChatwootClientConfig
from src.infrastructure.pymysql.connection import get_mysql_connection
from src.infrastructure.pymysql.contacts_repository import ContactsRepository
from src.shared.config import get_env, load_env_file
from src.shared.logger import get_logger
from src.use_cases.contacts_list import list_all_contacts
from src.use_cases.contacts_sync import sync_contacts
from src.use_cases.health_check import run_health_checks


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica conectividad con Chatwoot API y MySQL.")
    parser.add_argument("--json", action="store_true", help="Imprime salida en JSON.")
    parser.add_argument("--debug", action="store_true", help="Habilita logs de depuración.")
    parser.add_argument("--sync-contacts", action="store_true", help="Descarga contactos a MySQL.")
    parser.add_argument("--list-contacts", action="store_true", help="Lista contactos desde Chatwoot API.")
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

    if args.sync_contacts and args.list_contacts:
        print("Error: usa solo una de estas opciones: --sync-contacts o --list-contacts.")
        sys.exit(1)

    if args.list_contacts:
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
            list_all_contacts(client, logger=logger, per_page=args.contacts_per_page)
        )
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
        sync_contacts(client, repo, logger=logger, per_page=args.contacts_per_page)
        conn.close()
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


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: max(0, width - 1)] + "…"


def _print_contacts_table(contacts) -> None:
    columns = [
        ("id", 10),
        ("name", 30),
        ("phone_number", 18),
        ("email", 30),
        ("identifier", 20),
        ("updated_at", 12),
    ]
    header = " | ".join(label.ljust(width) for label, width in columns)
    separator = "-+-".join("-" * width for _, width in columns)
    print(header)
    print(separator)
    for contact in contacts:
        row = []
        for key, width in columns:
            raw = contact.get(key)
            value = "" if raw is None else str(raw)
            value = _truncate(value, width)
            row.append(value.ljust(width))
        print(" | ".join(row))
