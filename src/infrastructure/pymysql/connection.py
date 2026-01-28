from __future__ import annotations

import pymysql

from src.entities.mysql_config import MySQLConfig


def get_mysql_connection(config: MySQLConfig) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=config.host,
        user=config.user,
        password=config.password,
        database=config.database,
        port=config.port,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=config.connect_timeout,
    )
