from __future__ import annotations

from typing import Optional

from src.infrastructure.chatwoot_api.client import ChatwootClient, ChatwootClientConfig
from src.infrastructure.mysql.connection import MySQLConfig, check_connection as check_mysql
from src.shared.config import get_env
from src.shared.logger import Logger, get_logger


def _build_chatwoot_config() -> Optional[ChatwootClientConfig]:
    base_url = get_env("CHATWOOT_BASE_URL")
    account_id = get_env("CHATWOOT_ACCOUNT_ID")
    api_token = get_env("CHATWOOT_API_ACCESS_TOKEN")
    if not base_url or not account_id or not api_token:
        return None
    return ChatwootClientConfig(base_url=base_url, account_id=account_id, api_token=api_token)


def _build_mysql_config() -> Optional[MySQLConfig]:
    host = get_env("MYSQL_HOST")
    user = get_env("MYSQL_USER")
    password = get_env("MYSQL_PASSWORD")
    database = get_env("MYSQL_DB")
    port_raw = get_env("MYSQL_PORT")
    if not host or not user or not password or not database:
        return None
    port = int(port_raw) if port_raw else 3306
    return MySQLConfig(host=host, user=user, password=password, database=database, port=port)


def run_health_checks(logger: Optional[Logger] = None) -> dict:
    logger = logger or get_logger("health")
    results: dict = {"chatwoot": None, "mysql": None}

    chatwoot_config = _build_chatwoot_config()
    if chatwoot_config:
        client = ChatwootClient(chatwoot_config, logger=logger)
        results["chatwoot"] = client.check_connection()
    else:
        results["chatwoot"] = {"ok": False, "error": "Missing Chatwoot env vars"}

    mysql_config = _build_mysql_config()
    if mysql_config:
        results["mysql"] = check_mysql(mysql_config, logger=logger)
    else:
        results["mysql"] = {"ok": False, "error": "Missing MySQL env vars"}

    results["ok"] = bool(results["chatwoot"]["ok"] and results["mysql"]["ok"])
    return results
