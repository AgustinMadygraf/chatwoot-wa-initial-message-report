from __future__ import annotations

from dataclasses import dataclass

import pymysql

from shared.logger import Logger, get_logger


@dataclass
class MySQLConfig:
    host: str
    user: str
    password: str
    database: str
    port: int = 3306
    connect_timeout: int = 5


def check_connection(config: MySQLConfig, logger: Logger | None = None) -> dict:
    logger = logger or get_logger("mysql")
    logger.debug(
        f"MySQL check: host={config.host} port={config.port} user={config.user} db={config.database} timeout={config.connect_timeout}"
    )
    try:
        conn = pymysql.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database,
            port=config.port,
            connect_timeout=config.connect_timeout,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        finally:
            conn.close()
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"MySQL check failed: {exc!r}")
        return {"ok": False, "error": str(exc)}
