from __future__ import annotations

from application.ports.health_check import HealthCheckPort, HealthCheckResults, HealthServiceStatus
from infrastructure.chatwoot_api.client import ChatwootClient, ChatwootClientConfig
from infrastructure.pymysql.health import MySQLConfig, check_connection as check_mysql
from shared.config import get_env
from shared.logger import Logger, get_logger


class EnvironmentHealthCheck(HealthCheckPort):
    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger or get_logger("health")

    def _build_chatwoot_config(self) -> ChatwootClientConfig | None:
        base_url = get_env("CHATWOOT_BASE_URL")
        account_id = get_env("CHATWOOT_ACCOUNT_ID")
        api_token = get_env("CHATWOOT_API_ACCESS_TOKEN")
        if not base_url or not account_id or not api_token:
            return None
        return ChatwootClientConfig(base_url=base_url, account_id=account_id, api_token=api_token)

    def _build_mysql_config(self) -> MySQLConfig | None:
        host = get_env("MYSQL_HOST")
        user = get_env("MYSQL_USER")
        password = get_env("MYSQL_PASSWORD")
        database = get_env("MYSQL_DB")
        port_raw = get_env("MYSQL_PORT")
        if not host or not user or not password or not database:
            return None
        port = int(port_raw) if port_raw else 3306
        return MySQLConfig(host=host, user=user, password=password, database=database, port=port)

    def check(self) -> HealthCheckResults:
        results: HealthCheckResults = {
            "ok": False,
            "chatwoot": {"ok": False, "error": "Sin verificar"},
            "mysql": {"ok": False, "error": "Sin verificar"},
        }

        chatwoot_config = self._build_chatwoot_config()
        if chatwoot_config:
            client = ChatwootClient(chatwoot_config, logger=self._logger)
            results["chatwoot"] = client.check_connection()
        else:
            results["chatwoot"] = {"ok": False, "error": "Missing Chatwoot env vars"}

        mysql_config = self._build_mysql_config()
        if mysql_config:
            results["mysql"] = check_mysql(mysql_config, logger=self._logger)
        else:
            results["mysql"] = {"ok": False, "error": "Missing MySQL env vars"}

        return results
