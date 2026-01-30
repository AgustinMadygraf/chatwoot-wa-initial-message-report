from __future__ import annotations

from typing import Protocol

from application.ports.mysql_admin import MySQLAdminPort
from entities.mysql_config import MySQLConfig


class MySQLAdminGateway(MySQLAdminPort, Protocol):
    def create_database(self, config: MySQLConfig) -> None:
        """Create database if not exists."""

    def check_connection(self, config: MySQLConfig) -> None:
        """Validate a connection to the configured database."""
