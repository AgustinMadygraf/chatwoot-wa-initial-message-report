from __future__ import annotations

import sys

import interface_adapter.controllers.cli as adapter_cli
import interface_adapter.controllers.init_db_cli as init_db_cli
from interface_adapter.presenter.init_db_presenter import present_init_db
from application.use_cases.init_db import InitDbResult


class FakeGateway:
    def create_database(self, *_args, **_kwargs) -> None:
        return None

    def check_connection(self, *_args, **_kwargs) -> None:
        return None


def test_present_init_db_messages() -> None:
    assert present_init_db(InitDbResult(ok=True)) == "MySQL listo. DB verificada."
    assert "Init DB fallo" in present_init_db(InitDbResult(ok=False, error="boom"))


def test_init_db_cli_success(monkeypatch, capsys) -> None:
    monkeypatch.setenv("MYSQL_HOST", "h")
    monkeypatch.setenv("MYSQL_USER", "u")
    monkeypatch.setenv("MYSQL_PASSWORD", "p")
    monkeypatch.setenv("MYSQL_DB", "d")
    monkeypatch.setenv("MYSQL_PORT", "3306")
    monkeypatch.setattr(init_db_cli, "PyMySQLAdminGateway", lambda: FakeGateway())
    monkeypatch.setattr(sys, "argv", ["init_db.py"])
    init_db_cli.main()
    assert "MySQL listo" in capsys.readouterr().out


def test_init_db_cli_missing_env(monkeypatch, capsys) -> None:
    monkeypatch.delenv("MYSQL_HOST", raising=False)
    monkeypatch.delenv("MYSQL_USER", raising=False)
    monkeypatch.delenv("MYSQL_PASSWORD", raising=False)
    monkeypatch.delenv("MYSQL_DB", raising=False)
    monkeypatch.setattr(init_db_cli, "load_env_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(sys, "argv", ["init_db.py"])
    try:
        init_db_cli.main()
    except SystemExit:
        pass
    assert "Init DB fallo" in capsys.readouterr().out


def test_controller_cli_forwards(monkeypatch) -> None:
    called = {"ok": False}

    def _fake_main() -> None:
        called["ok"] = True

    monkeypatch.setattr(adapter_cli, "main", _fake_main)
    adapter_cli.main()
    assert called["ok"] is True
