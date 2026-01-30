from __future__ import annotations

import pymysql
from pymysql.err import OperationalError

from entities.mysql_config import MySQLConfig


def get_mysql_connection(config: MySQLConfig) -> pymysql.connections.Connection:
    try:
        return _connect_with_db(config)
    except OperationalError as exc:
        if _is_missing_db_error(exc):
            _create_database(config)
            return _connect_with_db(config)
        raise


def _connect_with_db(config: MySQLConfig) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=config.host,
        user=config.user,
        password=config.password,
        database=config.database,
        port=config.port,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=config.connect_timeout,
    )


def _create_database(config: MySQLConfig) -> None:
    connection = pymysql.connect(
        host=config.host,
        user=config.user,
        password=config.password,
        port=config.port,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=config.connect_timeout,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config.database}` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "DEFAULT COLLATE utf8mb4_unicode_ci"
            )
    finally:
        connection.close()


def _is_missing_db_error(exc: OperationalError) -> bool:
    return bool(exc.args) and exc.args[0] == 1049
