from __future__ import annotations

from application.ports.chatwoot_client import ChatwootClientPort
from application.ports.repositories import AccountsRepositoryPort
from domain.chatwoot import Account
from shared.logger import Logger, get_logger


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
