from __future__ import annotations

from application.ports.unit_of_work import UnitOfWorkPort
from entities.mysql_config import MySQLConfig
from infrastructure.pymysql.connection import get_mysql_connection


class PyMySQLUnitOfWork(UnitOfWorkPort):
    def __init__(self, config: MySQLConfig) -> None:
        self._config = config
        self.connection = None

    def __enter__(self) -> "PyMySQLUnitOfWork":
        self.connection = get_mysql_connection(self._config)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.connection is None:
            return
        if exc_type:
            try:
                self.rollback()
            finally:
                self.connection.close()
            return
        try:
            self.commit()
        finally:
            self.connection.close()

    def commit(self) -> None:
        if self.connection is not None:
            self.connection.commit()

    def rollback(self) -> None:
        if self.connection is not None:
            self.connection.rollback()
