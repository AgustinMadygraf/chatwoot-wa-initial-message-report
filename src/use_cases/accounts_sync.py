from __future__ import annotations

from infrastructure.chatwoot_api.client import ChatwootClient
from infrastructure.pymysql.accounts_repository import AccountsRepository
from shared.logger import Logger, get_logger


def sync_account(
    client: ChatwootClient,
    repo: AccountsRepository,
    logger: Logger | None = None,
) -> dict[str, int]:
    logger = logger or get_logger("accounts")
    repo.ensure_table()

    payload = client.get_account_details()
    repo.upsert_account(payload)
    logger.info("Cuenta actualizada en MySQL.")
    return {"total_upserted": 1}
