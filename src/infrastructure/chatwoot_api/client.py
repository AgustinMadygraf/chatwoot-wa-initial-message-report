from __future__ import annotations

from dataclasses import dataclass

import requests

from src.shared.logger import Logger, get_logger


@dataclass
class ChatwootClientConfig:
    base_url: str
    account_id: str
    api_token: str
    timeout_seconds: float = 8.0


class ChatwootClient:
    def __init__(self, config: ChatwootClientConfig, logger: Logger | None = None) -> None:
        self._config = config
        self._logger = logger or get_logger("chatwoot")

    def list_inboxes(self) -> dict:
        url = (
            f"{self._config.base_url.rstrip('/')}/api/v1/accounts/{self._config.account_id}/inboxes"
        )
        headers = {"api_access_token": self._config.api_token}
        response = requests.get(url, headers=headers, timeout=self._config.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def list_conversations(
        self, *, page: int, per_page: int | None = None, status: str = "all"
    ) -> dict:
        url = (
            f"{self._config.base_url.rstrip('/')}/api/v1/accounts/"
            f"{self._config.account_id}/conversations"
        )
        headers = {"api_access_token": self._config.api_token}
        params = {"page": page, "status": status}
        if per_page:
            params["per_page"] = per_page
        response = requests.get(
            url, headers=headers, params=params, timeout=self._config.timeout_seconds
        )
        response.raise_for_status()
        return response.json()

    def list_conversation_messages(
        self, *, conversation_id: int, page: int, per_page: int | None = None
    ) -> dict:
        url = (
            f"{self._config.base_url.rstrip('/')}/api/v1/accounts/"
            f"{self._config.account_id}/conversations/{conversation_id}/messages"
        )
        headers = {"api_access_token": self._config.api_token}
        params = {"page": page}
        if per_page:
            params["per_page"] = per_page
        response = requests.get(
            url, headers=headers, params=params, timeout=self._config.timeout_seconds
        )
        response.raise_for_status()
        return response.json()

    def check_connection(self) -> dict:
        url = f"{self._config.base_url.rstrip('/')}/api/v1/accounts/{self._config.account_id}"
        headers = {"api_access_token": self._config.api_token}
        try:
            response = requests.get(url, headers=headers, timeout=self._config.timeout_seconds)
            if response.ok:
                return {"ok": True, "status_code": response.status_code}
            return {
                "ok": False,
                "status_code": response.status_code,
                "error": response.text[:200],
            }
        except requests.RequestException as exc:
            self._logger.warning(f"Chatwoot check failed: {exc}")
            return {"ok": False, "error": str(exc)}

    def get_account_details(self) -> dict:
        url = f"{self._config.base_url.rstrip('/')}/api/v1/accounts/{self._config.account_id}"
        headers = {"api_access_token": self._config.api_token}
        response = requests.get(url, headers=headers, timeout=self._config.timeout_seconds)
        response.raise_for_status()
        return response.json()
