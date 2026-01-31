import subprocess
from typing import Any, Mapping
from urllib.parse import urlparse

import httpx

from src.application.ports.ngrok_tunnel import NgrokTunnel
from src.shared import config
from src.shared.logger import get_logger

logger = get_logger(__name__)

LOCAL_API_BASE = "http://127.0.0.1:4040"


class NgrokCliTunnel(NgrokTunnel):
    def __init__(self, port: int | None = None, url_webhook: str | None = None):
        self.port = port if port is not None else config.get_port()
        self.url_webhook = url_webhook or config.get_url_webhook()

    def _extract_domain(self) -> str:
        raw = (self.url_webhook or "").strip()
        if not raw:
            raise RuntimeError("URL_WEBHOOK not set")
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        domain = parsed.netloc or parsed.path
        domain = domain.split("/")[0].strip()
        if not domain:
            raise RuntimeError("URL_WEBHOOK must include a domain")
        return domain

    def start(self) -> int:
        domain = self._extract_domain()
        cmd = ["ngrok", "http", str(self.port), "--domain", domain]
        logger.info("Starting ngrok tunnel", port=self.port, domain=domain)
        return subprocess.call(cmd)

    def status(self) -> Mapping[str, Any]:
        try:
            resp = httpx.get(f"{LOCAL_API_BASE}/api/tunnels", timeout=2)
            if resp.status_code >= 400:
                return {"running": False, "status": resp.status_code}
            data = resp.json()
            tunnels = data.get("tunnels", data) if isinstance(data, dict) else data
            return {"running": True, "tunnels": tunnels}
        except Exception as exc:
            logger.warning("Ngrok status check failed", error=str(exc))
            return {"running": False, "error": str(exc)}

    def stop(self) -> None:
        status = self.status()
        tunnels = status.get("tunnels") if isinstance(status, dict) else None
        if not tunnels:
            return
        if isinstance(tunnels, dict):
            tunnels = tunnels.get("tunnels", [])
        for tunnel in tunnels:
            name = tunnel.get("name") if isinstance(tunnel, dict) else None
            if not name:
                continue
            try:
                httpx.delete(f"{LOCAL_API_BASE}/api/tunnels/{name}", timeout=2)
            except Exception as exc:
                logger.warning("Failed to stop ngrok tunnel", name=name, error=str(exc))
