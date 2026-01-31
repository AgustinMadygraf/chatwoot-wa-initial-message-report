import httpx
from typing import Any, Dict, Tuple


class HttpxClient:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def post_json(self, url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Tuple[int, str]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
        return resp.status_code, resp.text
