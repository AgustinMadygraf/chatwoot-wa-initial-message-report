from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pymysql

from src.shared.logger import Logger, get_logger

@dataclass
class MySQLConfig:
    host: str
    user: str
    password: str
    database: str
    port: int = 3306
    connect_timeout: int = 5


def check_connection(config: MySQLConfig, logger: Optional[Logger] = None) -> dict:
    logger = logger or get_logger("mysql")
    logger.debug(
        "MySQL check: host=%s port=%s user=%s db=%s timeout=%s"
        % (
            config.host,
            config.port,
            config.user,
            config.database,
            config.connect_timeout,
        )
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
        logger.debug("MySQL check failed: %r" % (exc,))
        return {"ok": False, "error": str(exc)}
