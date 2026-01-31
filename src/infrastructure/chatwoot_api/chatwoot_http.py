from typing import Tuple

from src.application.ports.chatwoot_gateway import ChatwootGateway
from src.infrastructure.httpx.http_client import HttpxClient
from src.shared import config
from src.shared.logger import get_logger

logger = get_logger(__name__)


class ChatwootHTTPAdapter(ChatwootGateway):
    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: int = 10,
        client: HttpxClient | None = None,
    ):
        env_base_url = config.get_env("CHATWOOT_BASE_URL")
        env_token = config.get_env("CHATWOOT_BOT_TOKEN") or config.get_env("CHATWOOT_API_ACCESS_TOKEN")
        self.base_url = base_url or env_base_url or config.CHATWOOT_BASE_URL
        self.token = token or env_token or config.CHATWOOT_BOT_TOKEN
        self.timeout = timeout
        self.client = client or HttpxClient(timeout=timeout)

    async def send_message(self, account_id: int, conversation_id: int, content: str) -> Tuple[int, str]:
        if not self.base_url:
            raise RuntimeError("CHATWOOT_BASE_URL not set")
        url = f"{self.base_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        headers = {"api_access_token": self.token}
        body = {"content": content, "message_type": "outgoing"}

        logger.info("Sending message to Chatwoot", url=url)
        try:
            status, resp_text = await self.client.post_json(url, headers=headers, body=body)
        except Exception as exc:
            logger.exception("HTTP request error when sending to Chatwoot: %s", exc)
            raise

        logger.info("Chatwoot returned status", status=status)
        return status, resp_text
