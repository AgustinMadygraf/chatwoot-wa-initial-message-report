from __future__ import annotations

import argparse
import sys
from types import SimpleNamespace

import pytest

import infrastructure.cli.as400_cli as as400_cli
import infrastructure.health_check as health_mod
import infrastructure.pymysql.fetchers as fetchers
from infrastructure.pymysql.message_reader import MySQLMessageReader


class _FakeUow:
    def __init__(self) -> None:
        self.connection = object()
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1


def test_require_env(monkeypatch) -> None:
    monkeypatch.setattr(as400_cli, "get_env", lambda *_args, **_kwargs: "x")
    assert as400_cli._require_env("A") == "x"
    monkeypatch.setattr(as400_cli, "get_env", lambda *_args, **_kwargs: "")
    with pytest.raises(ValueError):
        as400_cli._require_env("A")


def test_show_menu(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda: "2")
    assert as400_cli._show_menu() == "2"


def test_handle_health(monkeypatch) -> None:
    monkeypatch.setattr(as400_cli, "EnvironmentHealthCheck", lambda **_kwargs: object())
    monkeypatch.setattr(as400_cli, "run_health_checks", lambda *_args, **_kwargs: {"ok": True})
    called = {"printed": False}
    monkeypatch.setattr(
        as400_cli, "print_health_screen", lambda _results: called.__setitem__("printed", True)
    )
    as400_cli._handle_health(logger=None)
    assert called["printed"] is True


def test_handle_list_functions(monkeypatch) -> None:
    monkeypatch.setattr(as400_cli, "_require_env", lambda _name: "10")
    monkeypatch.setattr(as400_cli, "fetch_inboxes", lambda _account_id: [{"id": 1}])
    monkeypatch.setattr(as400_cli, "fetch_conversations", lambda: [{"id": 2}])
    monkeypatch.setattr(as400_cli, "fetch_messages", lambda: [{"id": 3}])
    monkeypatch.setattr(as400_cli, "fetch_accounts", lambda: [{"id": 4}])
    monkeypatch.setattr(as400_cli, "print_inboxes_table", lambda *_a, **_k: None)
    monkeypatch.setattr(as400_cli, "print_conversations_table", lambda *_a, **_k: None)
    monkeypatch.setattr(as400_cli, "print_messages_table", lambda *_a, **_k: None)
    monkeypatch.setattr(as400_cli, "print_accounts_table", lambda *_a, **_k: None)
    as400_cli.handle_list_inboxes()
    as400_cli.handle_list_conversations()
    as400_cli.handle_list_messages()
    as400_cli.handle_list_accounts()


def test_handle_sync_happy_path(monkeypatch) -> None:
    monkeypatch.setattr(as400_cli, "_require_env", lambda _name: "1")
    monkeypatch.setattr(as400_cli, "get_env", lambda _name, default=None: default or "3306")
    monkeypatch.setattr(as400_cli, "ChatwootClient", lambda *_a, **_k: object())
    monkeypatch.setattr(as400_cli, "PyMySQLUnitOfWork", lambda *_a, **_k: _FakeUow())
    monkeypatch.setattr(as400_cli, "AccountsRepository", lambda _c: object())
    monkeypatch.setattr(as400_cli, "InboxesRepository", lambda _c, account_id: object())
    monkeypatch.setattr(as400_cli, "ConversationsRepository", lambda _c: object())
    monkeypatch.setattr(as400_cli, "MessagesRepository", lambda _c: object())
    monkeypatch.setattr(as400_cli, "sync_account", lambda *_a, **_k: {"total_upserted": 1})
    monkeypatch.setattr(as400_cli, "sync_inboxes", lambda *_a, **_k: {"total_upserted": 2})
    monkeypatch.setattr(as400_cli, "sync_conversations", lambda *_a, **_k: [11, 12])
    monkeypatch.setattr(as400_cli, "sync_messages", lambda *_a, **_k: {"total_upserted": 3})
    monkeypatch.setattr(as400_cli, "build_sync_progress_screen", lambda *_a, **_k: "screen")
    monkeypatch.setattr(as400_cli, "print_sync_screen", lambda *_a, **_k: None)

    class _Live:
        def __init__(self, *_a, **_k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def update(self, *_a, **_k):
            return None

    monkeypatch.setattr(as400_cli, "Live", _Live)
    args = argparse.Namespace(debug=False, per_page=None)
    as400_cli._handle_sync(args, logger=None)


def test_handle_sync_messages_only_paths(monkeypatch, capsys) -> None:
    monkeypatch.setattr(as400_cli, "_require_env", lambda _name: "1")
    monkeypatch.setattr(as400_cli, "get_env", lambda _name, default=None: default or "3306")
    monkeypatch.setattr(as400_cli, "ChatwootClient", lambda *_a, **_k: object())
    monkeypatch.setattr(as400_cli, "PyMySQLUnitOfWork", lambda *_a, **_k: _FakeUow())

    class _ConvRepoEmpty:
        def __init__(self, _conn):
            pass

        def ensure_table(self):
            return None

        def list_conversations(self):
            return []

    monkeypatch.setattr(as400_cli, "ConversationsRepository", _ConvRepoEmpty)
    monkeypatch.setattr(as400_cli, "MessagesRepository", lambda _c: SimpleNamespace(ensure_table=lambda: None))
    monkeypatch.setattr(as400_cli, "print_sync_screen", lambda *_a, **_k: None)
    args = argparse.Namespace(debug=False, per_page=None)
    as400_cli._handle_sync_messages_only(args, logger=None)
    assert "No hay conversaciones" in capsys.readouterr().out

    class _ConvRepoData(_ConvRepoEmpty):
        def list_conversations(self):
            return [{"id": 99, "account_id": 1, "inbox_id": 2}]

    monkeypatch.setattr(as400_cli, "ConversationsRepository", _ConvRepoData)
    monkeypatch.setattr(
        as400_cli,
        "sync_messages",
        lambda *_a, **_k: (_ for _ in ()).throw(ValueError("bad")),
    )
    with pytest.raises(RuntimeError):
        as400_cli._handle_sync_messages_only(args, logger=None)


def test_main_interactive_and_args(monkeypatch, capsys) -> None:
    monkeypatch.setattr(as400_cli, "load_env_file", lambda *_a, **_k: None)
    monkeypatch.setattr(as400_cli, "get_logger", lambda *_a, **_k: object())
    monkeypatch.setattr(sys, "argv", ["run.py"])
    choices = iter(["9", "0"])
    monkeypatch.setattr(as400_cli, "_show_menu", lambda: next(choices))
    as400_cli.main()
    assert "Opcion invalida" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["run.py", "--x"])
    monkeypatch.setattr(
        as400_cli,
        "_get_args",
        lambda: argparse.Namespace(
            sync=True,
            sync_messages=True,
            list_accounts=False,
            list_inboxes=False,
            list_conversations=False,
            list_messages=False,
            tui=False,
            json=False,
            debug=False,
            per_page=None,
        ),
    )
    with pytest.raises(SystemExit):
        as400_cli.main()


def test_main_other_branches(monkeypatch, capsys) -> None:
    monkeypatch.setattr(as400_cli, "load_env_file", lambda *_a, **_k: None)
    monkeypatch.setattr(as400_cli, "get_logger", lambda *_a, **_k: object())
    monkeypatch.setattr(sys, "argv", ["run.py", "--x"])

    # tui
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
            tui=True,
            json=False,
            debug=False,
            per_page=None,
        ),
    )
    ran = {"ok": False}

    class _App:
        def run(self):
            ran["ok"] = True

    monkeypatch.setattr(as400_cli, "As400App", _App)
    as400_cli.main()
    assert ran["ok"] is True

    # default health print
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
            json=False,
            debug=False,
            per_page=None,
        ),
    )
    monkeypatch.setattr(
        as400_cli,
        "run_health_checks",
        lambda *_a, **_k: {"ok": False, "chatwoot": {"ok": False}, "mysql": {"ok": True}},
    )
    monkeypatch.setattr(as400_cli, "EnvironmentHealthCheck", lambda **_k: object())
    as400_cli.main()
    out = capsys.readouterr().out
    assert "Estado general: ERROR" in out


def test_environment_health_check(monkeypatch) -> None:
    checker = health_mod.EnvironmentHealthCheck(logger=None)
    monkeypatch.setattr(health_mod, "get_env", lambda name: None)
    assert checker._build_chatwoot_config() is None
    assert checker._build_mysql_config() is None

    values = {
        "CHATWOOT_BASE_URL": "u",
        "CHATWOOT_ACCOUNT_ID": "1",
        "CHATWOOT_API_ACCESS_TOKEN": "t",
        "MYSQL_HOST": "h",
        "MYSQL_USER": "u",
        "MYSQL_PASSWORD": "p",
        "MYSQL_DB": "d",
        "MYSQL_PORT": "3306",
    }
    monkeypatch.setattr(health_mod, "get_env", lambda name: values.get(name))
    monkeypatch.setattr(health_mod, "ChatwootClient", lambda *_a, **_k: SimpleNamespace(check_connection=lambda: {"ok": True}))
    monkeypatch.setattr(health_mod, "check_mysql", lambda *_a, **_k: {"ok": True})
    result = checker.check()
    assert result["chatwoot"]["ok"] is True
    assert result["mysql"]["ok"] is True


def test_fetchers_and_message_reader(monkeypatch) -> None:
    monkeypatch.setattr(fetchers, "build_mysql_config", lambda: object())
    monkeypatch.setattr(fetchers, "PyMySQLUnitOfWork", lambda _cfg: _FakeUow())

    class _Repo:
        def __init__(self, _conn, **_kwargs):
            pass

        def ensure_table(self):
            return None

        def list_accounts(self):
            return [{"id": 1}]

        def list_inboxes(self):
            return [{"id": 2}]

        def list_conversations(self):
            return [{"id": 3}]

        def list_messages(self):
            return [{"id": 4}]

    monkeypatch.setattr(fetchers, "AccountsRepository", _Repo)
    monkeypatch.setattr(fetchers, "InboxesRepository", _Repo)
    monkeypatch.setattr(fetchers, "ConversationsRepository", _Repo)
    monkeypatch.setattr(fetchers, "MessagesRepository", _Repo)
    assert fetchers.fetch_accounts()[0]["id"] == 1
    assert fetchers.fetch_inboxes(1)[0]["id"] == 2
    assert fetchers.fetch_conversations()[0]["id"] == 3
    assert fetchers.fetch_messages()[0]["id"] == 4

    class _MsgRepo:
        def __init__(self, _conn):
            self.ensured = False

        def ensure_table(self):
            self.ensured = True

        def list_messages(self, limit=None):
            return [{"content": None, "conversation_id": 9, "created_at": 11}]

    monkeypatch.setattr(
        "infrastructure.pymysql.message_reader.MessagesRepository",
        _MsgRepo,
    )
    reader = MySQLMessageReader(connection=object(), ensure_table=True)
    rows = list(reader.list_messages(limit=5))
    assert rows[0].content == ""
    assert rows[0].conversation_id == 9
