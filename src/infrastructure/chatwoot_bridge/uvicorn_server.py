import uvicorn

from src.application.ports.webhook_bridge import WebhookBridgeServer
from src.shared.logger import get_logger

logger = get_logger(__name__)


class UvicornWebhookBridgeServer(WebhookBridgeServer):
    def __init__(self, app_import: str | None = None):
        self.app_import = app_import or "src.interface_adapter.presenters.webhook_api:app"

    def run(self, host: str, port: int, reload: bool) -> int:
        logger.info("Starting webhook bridge", host=host, port=port, reload=reload)
        uvicorn.run(self.app_import, host=host, port=port, reload=reload)
        return 0
