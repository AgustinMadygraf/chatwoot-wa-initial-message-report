from __future__ import annotations

import pymysql

from src.entities.mysql_config import MySQLConfig
from src.interface_adapter.gateways.mysql_admin_gateway import MySQLAdminGateway


class PyMySQLAdminGateway(MySQLAdminGateway):
    def create_database(self, config: MySQLConfig) -> None:
        safe_db = config.database.replace("`", "``")
        conn = pymysql.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            port=config.port,
            connect_timeout=config.connect_timeout,
            autocommit=True,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{safe_db}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
        finally:
            conn.close()

    def check_connection(self, config: MySQLConfig) -> None:
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
