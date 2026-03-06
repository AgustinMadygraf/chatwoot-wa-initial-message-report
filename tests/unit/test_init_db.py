from __future__ import annotations

from entities.mysql_config import MySQLConfig
from use_cases.init_db import run_init_db


class FakeGateway:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.created: list[MySQLConfig] = []
        self.checked: list[MySQLConfig] = []

    def create_database(self, config: MySQLConfig) -> None:
        self.created.append(config)
        if self.fail:
            raise RuntimeError("create failed")

    def check_connection(self, config: MySQLConfig) -> None:
        self.checked.append(config)
        if self.fail:
            raise RuntimeError("check failed")


def test_run_init_db_success() -> None:
    gateway = FakeGateway()
    config = MySQLConfig(host="h", user="u", password="p", database="d")
    result = run_init_db(config, gateway)
    assert result.ok is True
    assert gateway.created == [config]
    assert gateway.checked == [config]


def test_run_init_db_failure() -> None:
    gateway = FakeGateway(fail=True)
    config = MySQLConfig(host="h", user="u", password="p", database="d")
    result = run_init_db(config, gateway)
    assert result.ok is False
    assert result.error is not None
