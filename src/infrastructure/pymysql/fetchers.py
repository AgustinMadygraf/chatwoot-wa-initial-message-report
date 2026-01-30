from __future__ import annotations

from infrastructure.pymysql.accounts_repository import AccountsRepository
from infrastructure.pymysql.conversations_repository import ConversationsRepository
from infrastructure.pymysql.inboxes_repository import InboxesRepository
from infrastructure.pymysql.messages_repository import MessagesRepository
from infrastructure.pymysql.unit_of_work import PyMySQLUnitOfWork
from shared.config import build_mysql_config


def fetch_accounts() -> list[dict[str, object]]:
    config = build_mysql_config()
    with PyMySQLUnitOfWork(config) as uow:
        repo = AccountsRepository(uow.connection)
        repo.ensure_table()
        return repo.list_accounts()


def fetch_inboxes(account_id: int) -> list[dict[str, object]]:
    config = build_mysql_config()
    with PyMySQLUnitOfWork(config) as uow:
        repo = InboxesRepository(uow.connection, account_id=account_id)
        repo.ensure_table()
        return repo.list_inboxes()


def fetch_conversations() -> list[dict[str, object]]:
    config = build_mysql_config()
    with PyMySQLUnitOfWork(config) as uow:
        repo = ConversationsRepository(uow.connection)
        repo.ensure_table()
        return repo.list_conversations()


def fetch_messages() -> list[dict[str, object]]:
    config = build_mysql_config()
    with PyMySQLUnitOfWork(config) as uow:
        repo = MessagesRepository(uow.connection)
        repo.ensure_table()
        return repo.list_messages()
