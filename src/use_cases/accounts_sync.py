from __future__ import annotations

from typing import Dict, Optional

from src.infrastructure.chatwoot_api.client import ChatwootClient
from src.infrastructure.pymysql.accounts_repository import AccountsRepository
from src.shared.logger import Logger, get_logger


def sync_account(
    client: ChatwootClient,
    repo: AccountsRepository,
    logger: Optional[Logger] = None,
) -> Dict[str, int]:
    logger = logger or get_logger("accounts")
    repo.ensure_table()

    payload = client.get_account_details()
    repo.upsert_account(payload)
    logger.info("Cuenta actualizada en MySQL.")
    return {"total_upserted": 1}
