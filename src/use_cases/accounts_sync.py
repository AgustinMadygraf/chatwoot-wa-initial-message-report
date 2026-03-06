from __future__ import annotations

from use_cases.ports.chatwoot_client import ChatwootClientPort
from use_cases.ports.repositories import AccountsRepositoryPort
from entities.chatwoot import Account
from infrastructure.logging.logger import Logger, get_logger


def sync_account(
    client: ChatwootClientPort,
    repo: AccountsRepositoryPort,
    logger: Logger | None = None,
) -> dict[str, int]:
    logger = logger or get_logger("accounts")
    repo.ensure_table()

    payload = client.get_account_details()
    account = Account.from_payload(payload)
    repo.upsert_account(account.to_record())
    logger.info("Cuenta actualizada en MySQL.")
    return {"total_upserted": 1}
