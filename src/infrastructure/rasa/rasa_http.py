from typing import List, Sequence

from src.application.ports.rasa_gateway import RasaGateway
from src.infrastructure.httpx.http_client import HttpxClient
from src.shared import config
from src.shared.logger import get_logger

logger = get_logger(__name__)


class RasaHTTPGateway(RasaGateway):
    def __init__(self, base_url: str | None = None, client: HttpxClient | None = None, timeout: int = 10):
        self.base_url = base_url or config.RASA_REST_URL
        self.client = client or HttpxClient(timeout=timeout)

    async def send_message(self, sender_id: str, text: str) -> Sequence[str]:
        if not self.base_url:
            raise RuntimeError("RASA_REST_URL not set")
        body = {"sender": sender_id, "message": text}
        logger.info("Sending message to Rasa", sender_id=sender_id)
        status, resp_text = await self.client.post_json(self.base_url, headers={}, body=body)

        if status >= 400:
            raise RuntimeError(f"Rasa error status={status}")

        try:
            import json

            data = json.loads(resp_text)
            if isinstance(data, list):
                texts: List[str] = []
                for item in data:
                    text_val = item.get("text") if isinstance(item, dict) else None
                    if text_val:
                        texts.append(str(text_val))
                return texts
        except Exception:
            logger.exception("Failed to parse Rasa response")

        return []
