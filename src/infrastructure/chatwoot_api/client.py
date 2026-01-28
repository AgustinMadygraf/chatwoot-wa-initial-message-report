from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from src.shared.logger import get_logger, Logger


@dataclass
class ChatwootClientConfig:
    base_url: str
    account_id: str
    api_token: str
    timeout_seconds: float = 8.0


class ChatwootClient:
    def __init__(self, config: ChatwootClientConfig, logger: Optional[Logger] = None) -> None:
        self._config = config
        self._logger = logger or get_logger("chatwoot")

    def list_contacts(self, page: int, per_page: Optional[int] = None) -> dict:
        url = (
            f"{self._config.base_url.rstrip('/')}/api/v1/accounts/"
            f"{self._config.account_id}/contacts"
        )
        headers = {"api_access_token": self._config.api_token}
        params = {"page": page}
        if per_page:
            params["per_page"] = per_page
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=self._config.timeout_seconds,
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
