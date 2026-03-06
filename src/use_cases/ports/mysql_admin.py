from __future__ import annotations

from typing import Protocol


class MySQLAdminPort(Protocol):
    def create_database(self, config) -> None: ...

    def check_connection(self, config) -> None: ...
