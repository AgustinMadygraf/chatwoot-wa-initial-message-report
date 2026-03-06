from __future__ import annotations

import argparse
import sys

import pytest

import infrastructure.cli.as400_cli as as400_cli
import infrastructure.cli.cli as cli
import infrastructure.pymysql.connection as conn_mod
from entities.mysql_config import MySQLConfig


def test_as400_get_args_and_main_error_branches(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--list-inboxes", "--per-page", "10"])
    parsed = as400_cli._get_args()
    assert parsed.list_inboxes is True
    assert parsed.per_page == 10

    monkeypatch.setattr(as400_cli, "load_env_file", lambda *_a, **_k: None)
    monkeypatch.setattr(as400_cli, "get_logger", lambda *_a, **_k: object())
    monkeypatch.setattr(sys, "argv", ["prog", "--x"])

    # list handlers with exceptions
    monkeypatch.setattr(
        as400_cli,
        "_get_args",
        lambda: argparse.Namespace(
            sync=False,
            sync_messages=False,
            list_accounts=False,
            list_inboxes=True,
            list_conversations=False,
            list_messages=False,
            tui=False,
            json=False,
            debug=False,
            per_page=None,
        ),
    )
    monkeypatch.setattr(as400_cli, "handle_list_inboxes", lambda: (_ for _ in ()).throw(ValueError("x")))
    with pytest.raises(SystemExit):
        as400_cli.main()
    assert "Listar inboxes fallo" in capsys.readouterr().out

    monkeypatch.setattr(
        as400_cli,
        "_get_args",
        lambda: argparse.Namespace(
            sync=False,
            sync_messages=False,
            list_accounts=False,
            list_inboxes=False,
            list_conversations=False,
            list_messages=False,
            tui=False,
            json=True,
            debug=False,
            per_page=None,
        ),
    )
    monkeypatch.setattr(as400_cli, "EnvironmentHealthCheck", lambda **_k: object())
    monkeypatch.setattr(
        as400_cli,
        "run_health_checks",
        lambda *_a, **_k: {"ok": True, "chatwoot": {"ok": True}, "mysql": {"ok": True}},
    )
    as400_cli.main()
    assert '"ok": true' in capsys.readouterr().out.lower()


def test_cli_get_args_and_error_branches(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--sync-messages", "--test", "12"])
    parsed = cli._get_args()
    assert parsed.sync_messages is True
    assert parsed.test == 12

    monkeypatch.setattr(cli, "load_env_file", lambda *_a, **_k: None)
    monkeypatch.setattr(cli, "get_logger", lambda *_a, **_k: object())
    monkeypatch.setattr(sys, "argv", ["prog", "--x"])

    monkeypatch.setattr(
        cli,
        "_get_args",
        lambda: argparse.Namespace(
            sync=False,
            sync_messages=False,
            list_accounts=False,
            list_inboxes=False,
            list_conversations=False,
            list_messages=False,
            tui=False,
            json=False,
            debug=False,
            test=1,
            per_page=None,
        ),
    )
    with pytest.raises(SystemExit):
        cli.main()
    assert "--test solo es valido" in capsys.readouterr().out

    monkeypatch.setattr(
        cli,
        "_get_args",
        lambda: argparse.Namespace(
            sync=False,
            sync_messages=False,
            list_accounts=False,
            list_inboxes=False,
            list_conversations=False,
            list_messages=False,
            tui=True,
            json=False,
            debug=False,
            test=None,
            per_page=None,
        ),
    )

    class _App:
        def run(self):
            return None

    monkeypatch.setattr(cli, "As400App", _App)
    cli.main()


def test_cli_sync_plain_and_sync_messages_only_branches(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_require_env", lambda _name: "1")
    monkeypatch.setattr(cli, "get_env", lambda _name, default=None: default or "3306")
    monkeypatch.setattr(cli, "ChatwootClient", lambda *_a, **_k: object())

    class _Uow:
        def __init__(self):
            self.connection = object()
            self.commits = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def commit(self):
            self.commits += 1

    monkeypatch.setattr(cli, "PyMySQLUnitOfWork", lambda *_a, **_k: _Uow())
    monkeypatch.setattr(cli, "AccountsRepository", lambda _c: object())
    monkeypatch.setattr(cli, "InboxesRepository", lambda _c, account_id: object())
    monkeypatch.setattr(cli, "ConversationsRepository", lambda _c: type("R", (), {"ensure_table": lambda self: None, "list_conversations": lambda self: []})())
    monkeypatch.setattr(cli, "MessagesRepository", lambda _c: type("R", (), {"ensure_table": lambda self: None})())
    monkeypatch.setattr(cli, "sync_account", lambda *_a, **_k: {"total_upserted": 1})
    monkeypatch.setattr(cli, "sync_inboxes", lambda *_a, **_k: {"total_upserted": 1})
    monkeypatch.setattr(cli, "sync_conversations", lambda *_a, **_k: [1])
    monkeypatch.setattr(cli, "sync_messages", lambda *_a, **_k: {"total_upserted": 1})

    args = argparse.Namespace(debug=False, per_page=None, test=None)
    cli._handle_sync_plain(args, logger=None)
    cli._handle_sync_messages_only(args, logger=None)
    assert "No hay conversaciones" in capsys.readouterr().out


def test_connection_missing_db_flow(monkeypatch) -> None:
    config = MySQLConfig(host="h", user="u", password="p", database="d", port=3306)
    calls = {"n": 0}

    class _Conn:
        def cursor(self):
            class _Cur:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return None

                def execute(self, _sql):
                    return None

            return _Cur()

        def close(self):
            return None

    def _connect(**_kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise conn_mod.OperationalError(1049, "missing")
        return _Conn()

    monkeypatch.setattr(conn_mod.pymysql, "connect", _connect)
    conn = conn_mod.get_mysql_connection(config)
    assert conn is not None
    assert conn_mod._is_missing_db_error(conn_mod.OperationalError(1049, "x")) is True
