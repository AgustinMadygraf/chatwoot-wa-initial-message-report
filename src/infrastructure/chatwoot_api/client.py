import time
from typing import Any, Dict, Optional

import requests

from shared.logger import Logger


class ChatwootClient:
    def __init__(
        self,
        base_url: str,
        account_id: str,
        api_token: str,
        timeout: int = 30,
        min_sleep: float = 0.15,
        logger: Optional[Logger] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.account_id = account_id
        self.timeout = timeout
        self.min_sleep = min_sleep
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({"api_access_token": api_token})

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        backoff = 1.0
        for attempt in range(5):
            if self.min_sleep:
                time.sleep(self.min_sleep)
            try:
                if self.logger:
                    self.logger.debug(f"{method} {url} params={params}")
                resp = self.session.request(method, url, params=params, timeout=self.timeout)
            except requests.RequestException:
                if attempt == 4:
                    raise
                time.sleep(backoff)
                backoff *= 2
                continue

            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                if attempt == 4:
                    resp.raise_for_status()
                if self.logger:
                    self.logger.warning(f"Retryable status {resp.status_code} for {url}")
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        time.sleep(float(retry_after))
                    except ValueError:
                        time.sleep(backoff)
                else:
                    time.sleep(backoff)
                backoff *= 2
                continue

            resp.raise_for_status()
            return resp.json()

        raise RuntimeError("Request failed after retries")

    def list_conversations(
        self,
        inbox_id: str,
        page: int,
        status: str = "all",
        per_page: Optional[int] = None,
        agent_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"status": status, "page": page}
        if inbox_id:
            params["inbox_id"] = inbox_id
        if per_page:
            params["per_page"] = per_page
        if agent_id:
            params["agent_id"] = agent_id
        return self._request(
            "GET",
            f"/api/v1/accounts/{self.account_id}/conversations",
            params=params,
        )

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/api/v1/accounts/{self.account_id}/conversations/{conversation_id}",
        )

    def list_inbox_members(self, inbox_id: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/api/v1/accounts/{self.account_id}/inbox_members/{inbox_id}",
        )
