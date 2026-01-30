from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import requests

from application.use_cases.accounts_sync import sync_account
from application.use_cases.conversations_sync import _extract_conversations, sync_conversations
from application.use_cases.inboxes_sync import _extract_inboxes, sync_inboxes
from application.use_cases.messages_sync import _extract_messages, sync_messages


class FakeAccountsRepo:
    def __init__(self) -> None:
        self.ensure_called = False
        self.upserts: list[dict[str, Any]] = []

    def ensure_table(self) -> None:
        self.ensure_called = True

    def upsert_account(self, payload: dict[str, Any]) -> None:
        self.upserts.append(payload)


class FakeInboxesRepo:
    def __init__(self) -> None:
        self.ensure_called = False
        self.upserts: list[dict[str, Any]] = []

    def ensure_table(self) -> None:
        self.ensure_called = True

    def upsert_inbox(self, payload: dict[str, Any]) -> None:
        self.upserts.append(payload)


class FakeConversationsRepo:
    def __init__(self) -> None:
        self.ensure_called = False
        self.upserts: list[dict[str, Any]] = []

    def ensure_table(self) -> None:
        self.ensure_called = True

    def upsert_conversation(self, payload: dict[str, Any]) -> None:
        self.upserts.append(payload)


class FakeMessagesRepo:
    def __init__(self) -> None:
        self.ensure_called = False
        self.upserts: list[dict[str, Any]] = []

    def ensure_table(self) -> None:
        self.ensure_called = True

    def upsert_message(self, payload: dict[str, Any]) -> None:
        self.upserts.append(payload)


class FakeClient:
    def __init__(self) -> None:
        self.inboxes_payload: dict[str, Any] = {"payload": []}
        self.conversations_pages: dict[int, dict[str, Any]] = {}
        self.messages_pages: dict[tuple[int, int], dict[str, Any]] = {}
        self.account_payload: dict[str, Any] = {"id": 1}
        self.raise_conversations: dict[int, Exception] = {}
        self.raise_messages: dict[tuple[int, int], Exception] = {}

    def get_account_details(self) -> dict[str, Any]:
        return self.account_payload

    def list_inboxes(self) -> dict[str, Any]:
        return self.inboxes_payload

    def list_conversations(self, *, page: int, per_page: int | None = None) -> dict[str, Any]:
        exc = self.raise_conversations.get(page)
        if exc:
            raise exc
        return self.conversations_pages.get(page, {"payload": []})

    def list_conversation_messages(
        self, *, conversation_id: int, page: int, per_page: int | None = None
    ) -> dict[str, Any]:
        exc = self.raise_messages.get((conversation_id, page))
        if exc:
            raise exc
        return self.messages_pages.get((conversation_id, page), {"payload": []})


def test_sync_account_upserts_once() -> None:
    client = FakeClient()
    repo = FakeAccountsRepo()
    result = sync_account(client, repo)
    assert repo.ensure_called is True
    assert repo.upserts == [
        {
            "id": 1,
            "name": None,
            "locale": None,
            "status": None,
            "created_at": None,
        }
    ]
    assert result["total_upserted"] == 1


def test_sync_inboxes_from_payload_list() -> None:
    client = FakeClient()
    client.inboxes_payload = {"payload": [{"id": 1}, {"id": 2}]}
    repo = FakeInboxesRepo()
    result = sync_inboxes(client, repo)
    assert repo.ensure_called is True
    assert len(repo.upserts) == 2
    assert repo.upserts[0]["id"] == 1
    assert result["total_upserted"] == 2
    assert list(_extract_inboxes({"data": [{"id": 3}]})) == [{"id": 3}]


def test_sync_conversations_paginates_and_reports_progress() -> None:
    client = FakeClient()
    client.conversations_pages = {
        1: {"payload": [{"id": 10}, {"id": None}, {"id": 11}]},
        2: {"payload": []},
    }
    repo = FakeConversationsRepo()
    progress_calls: list[tuple[int, int]] = []

    def progress(page: int, total: int) -> None:
        progress_calls.append((page, total))

    convo_ids = sync_conversations(client, repo, progress=progress)
    assert repo.ensure_called is True
    assert convo_ids == [10, 11]
    assert progress_calls == [(1, 2)]
    assert list(_extract_conversations({"data": {"payload": [{"id": 1}]}})) == [{"id": 1}]


def test_sync_conversations_handles_request_exception() -> None:
    client = FakeClient()
    client.raise_conversations[1] = requests.RequestException("boom")
    repo = FakeConversationsRepo()
    convo_ids = sync_conversations(client, repo)
    assert convo_ids == []


def test_sync_messages_counts_total_and_errors() -> None:
    client = FakeClient()
    client.messages_pages = {
        (99, 1): {"payload": [{"id": 1}, {"id": 2}]},
        (99, 2): {"payload": []},
    }
    repo = FakeMessagesRepo()
    result = sync_messages(client, repo, conversation_ids=[99])
    assert repo.ensure_called is True
    assert result["total_upserted"] == 2
    assert result["total_errors"] == 0
    assert list(_extract_messages({"data": [{"id": 9}]})) == [{"id": 9}]


def test_sync_messages_handles_request_exception() -> None:
    client = FakeClient()
    client.raise_messages[(5, 1)] = requests.RequestException("boom")
    repo = FakeMessagesRepo()
    result = sync_messages(client, repo, conversation_ids=[5])
    assert result["total_upserted"] == 0
    assert result["total_errors"] == 1
