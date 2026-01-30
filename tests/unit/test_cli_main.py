from __future__ import annotations

import json
import sys
from typing import Any

import infrastructure.CLI.cli as cli


class DummyLive:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self) -> "DummyLive":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def update(self, *_args, **_kwargs) -> None:
        return None


class FakeRepo:
    def __init__(self, *_args, **_kwargs) -> None:
        self.ensure_called = False

    def ensure_table(self) -> None:
        self.ensure_called = True

    def list_inboxes(self) -> list[dict[str, Any]]:
        return [{"id": 1}]

    def list_conversations(self) -> list[dict[str, Any]]:
        return [{"id": 1}]

    def list_messages(self) -> list[dict[str, Any]]:
        return [{"id": 1}]

    def list_accounts(self) -> list[dict[str, Any]]:
        return [{"id": 1}]


class FakeChatwootClient:
    def __init__(self, *_args, **_kwargs) -> None:
        pass


class FakeConn:
    def close(self) -> None:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


class _FakeUow:
    def __init__(self) -> None:
        self.connection = FakeConn()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FailingUow:
    def __enter__(self):
        raise RuntimeError("boom")

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _set_env(monkeypatch) -> None:
    monkeypatch.setenv("CHATWOOT_BASE_URL", "https://chatwoot.local")
    monkeypatch.setenv("CHATWOOT_ACCOUNT_ID", "1")
    monkeypatch.setenv("CHATWOOT_API_ACCESS_TOKEN", "token")
    monkeypatch.setenv("MYSQL_HOST", "localhost")
    monkeypatch.setenv("MYSQL_USER", "root")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")
    monkeypatch.setenv("MYSQL_DB", "db")
    monkeypatch.setenv("MYSQL_PORT", "3306")


def test_cli_health_screen(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "run_health_checks", lambda *_args, **_kwargs: {"ok": True})
    monkeypatch.setattr(cli, "print_health_screen", lambda results: print("HEALTH"))
    monkeypatch.setattr(sys, "argv", ["run_cli.py"])
    choices = iter(["1", "0"])
    monkeypatch.setattr(cli, "_show_menu", lambda: next(choices))
    cli.main()
    assert "HEALTH" in capsys.readouterr().out


def test_cli_json_health(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli,
        "run_health_checks",
        lambda *_args, **_kwargs: {"ok": True, "chatwoot": {"ok": True}, "mysql": {"ok": True}},
    )
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--json"])
    cli.main()
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["ok"] is True


def test_cli_list_inboxes(monkeypatch) -> None:
    _set_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--list-inboxes"])
    monkeypatch.setattr(cli, "InboxesRepository", FakeRepo)
    monkeypatch.setattr(cli, "PyMySQLUnitOfWork", lambda *_args, **_kwargs: _FakeUow())
    monkeypatch.setattr(cli, "print_inboxes_table", lambda *_args, **_kwargs: None)
    cli.main()


def test_cli_list_conversations(monkeypatch) -> None:
    _set_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--list-conversations"])
    monkeypatch.setattr(cli, "ConversationsRepository", FakeRepo)
    monkeypatch.setattr(cli, "PyMySQLUnitOfWork", lambda *_args, **_kwargs: _FakeUow())
    monkeypatch.setattr(cli, "print_conversations_table", lambda *_args, **_kwargs: None)
    cli.main()


def test_cli_list_messages(monkeypatch) -> None:
    _set_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--list-messages"])
    monkeypatch.setattr(cli, "MessagesRepository", FakeRepo)
    monkeypatch.setattr(cli, "PyMySQLUnitOfWork", lambda *_args, **_kwargs: _FakeUow())
    monkeypatch.setattr(cli, "print_messages_table", lambda *_args, **_kwargs: None)
    cli.main()


def test_cli_list_accounts(monkeypatch) -> None:
    _set_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--list-accounts"])
    monkeypatch.setattr(cli, "AccountsRepository", FakeRepo)
    monkeypatch.setattr(cli, "PyMySQLUnitOfWork", lambda *_args, **_kwargs: _FakeUow())
    monkeypatch.setattr(cli, "print_accounts_table", lambda *_args, **_kwargs: None)
    cli.main()


def test_cli_sync(monkeypatch) -> None:
    _set_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--sync"])
    monkeypatch.setattr(cli, "ChatwootClient", FakeChatwootClient)
    monkeypatch.setattr(cli, "PyMySQLUnitOfWork", lambda *_args, **_kwargs: _FakeUow())
    monkeypatch.setattr(cli, "AccountsRepository", FakeRepo)
    monkeypatch.setattr(cli, "InboxesRepository", FakeRepo)
    monkeypatch.setattr(cli, "ConversationsRepository", FakeRepo)
    monkeypatch.setattr(cli, "MessagesRepository", FakeRepo)
    monkeypatch.setattr(cli, "Live", DummyLive)
    monkeypatch.setattr(cli, "build_sync_progress_screen", lambda *_args, **_kwargs: "screen")
    monkeypatch.setattr(cli, "print_sync_screen", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "sync_account", lambda *_args, **_kwargs: {"total_upserted": 1})
    monkeypatch.setattr(cli, "sync_inboxes", lambda *_args, **_kwargs: {"total_upserted": 1})
    monkeypatch.setattr(cli, "sync_conversations", lambda *_args, **_kwargs: [1, 2])
    monkeypatch.setattr(
        cli, "sync_messages", lambda *_args, **_kwargs: {"total_upserted": 1}
    )
    cli.main()


def test_cli_multiple_args(monkeypatch, capsys) -> None:
    _set_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--list-accounts", "--list-inboxes"])
    try:
        cli.main()
    except SystemExit:
        pass
    assert "usa solo una opcion" in capsys.readouterr().out


def test_cli_list_inboxes_missing_env(monkeypatch, capsys) -> None:
    monkeypatch.delenv("MYSQL_HOST", raising=False)
    monkeypatch.setattr(cli, "load_env_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--list-inboxes"])
    try:
        cli.main()
    except SystemExit:
        pass
    assert "Listar inboxes fallo" in capsys.readouterr().out


def test_cli_list_conversations_missing_env(monkeypatch, capsys) -> None:
    monkeypatch.delenv("MYSQL_HOST", raising=False)
    monkeypatch.setattr(cli, "load_env_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--list-conversations"])
    try:
        cli.main()
    except SystemExit:
        pass
    assert "Listar conversaciones fallo" in capsys.readouterr().out


def test_cli_list_messages_missing_env(monkeypatch, capsys) -> None:
    monkeypatch.delenv("MYSQL_HOST", raising=False)
    monkeypatch.setattr(cli, "load_env_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--list-messages"])
    try:
        cli.main()
    except SystemExit:
        pass
    assert "Listar mensajes fallo" in capsys.readouterr().out


def test_cli_list_accounts_missing_env(monkeypatch, capsys) -> None:
    monkeypatch.delenv("MYSQL_HOST", raising=False)
    monkeypatch.setattr(cli, "load_env_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--list-accounts"])
    try:
        cli.main()
    except SystemExit:
        pass
    assert "Listar cuentas fallo" in capsys.readouterr().out


def test_cli_sync_mysql_connection_error(monkeypatch, capsys) -> None:
    _set_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--sync"])
    monkeypatch.setattr(cli, "ChatwootClient", FakeChatwootClient)
    monkeypatch.setattr(cli, "PyMySQLUnitOfWork", lambda *_args, **_kwargs: _FailingUow())
    try:
        cli.main()
    except SystemExit:
        pass
    assert "Sync fallo" in capsys.readouterr().out


def test_cli_status_non_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli,
        "run_health_checks",
        lambda *_args, **_kwargs: {
            "ok": False,
            "chatwoot": {"ok": False, "error": "x"},
            "mysql": {"ok": True},
        },
    )
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--debug"])
    cli.main()
    out = capsys.readouterr().out
    assert "Estado general" in out
    assert "chatwoot: ERROR" in out


def test_cli_sync_keyboard_interrupt(monkeypatch, capsys) -> None:
    _set_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--sync"])
    monkeypatch.setattr(cli, "ChatwootClient", FakeChatwootClient)
    monkeypatch.setattr(cli, "PyMySQLUnitOfWork", lambda *_args, **_kwargs: _FakeUow())
    monkeypatch.setattr(cli, "AccountsRepository", FakeRepo)
    monkeypatch.setattr(cli, "InboxesRepository", FakeRepo)
    monkeypatch.setattr(cli, "ConversationsRepository", FakeRepo)
    monkeypatch.setattr(cli, "MessagesRepository", FakeRepo)
    monkeypatch.setattr(cli, "Live", DummyLive)
    monkeypatch.setattr(cli, "build_sync_progress_screen", lambda *_args, **_kwargs: "screen")
    monkeypatch.setattr(cli, "print_sync_screen", lambda *_args, **_kwargs: None)

    def _raise(*_args, **_kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(cli, "sync_account", _raise)
    cli.main()
    assert "Sync cancelado" in capsys.readouterr().out


def test_cli_sync_exception(monkeypatch, capsys) -> None:
    _set_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_cli.py", "--sync"])
    monkeypatch.setattr(cli, "ChatwootClient", FakeChatwootClient)
    monkeypatch.setattr(cli, "PyMySQLUnitOfWork", lambda *_args, **_kwargs: _FakeUow())
    monkeypatch.setattr(cli, "AccountsRepository", FakeRepo)
    monkeypatch.setattr(cli, "InboxesRepository", FakeRepo)
    monkeypatch.setattr(cli, "ConversationsRepository", FakeRepo)
    monkeypatch.setattr(cli, "MessagesRepository", FakeRepo)
    monkeypatch.setattr(cli, "Live", DummyLive)
    monkeypatch.setattr(cli, "build_sync_progress_screen", lambda *_args, **_kwargs: "screen")
    monkeypatch.setattr(cli, "print_sync_screen", lambda *_args, **_kwargs: None)

    def _raise(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "sync_account", _raise)
    cli.main()
    assert "Sync fallo" in capsys.readouterr().out
