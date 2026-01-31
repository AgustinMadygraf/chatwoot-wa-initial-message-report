from src.application.ports.webhook_bridge import WebhookBridgeServer
from src.application.use_cases.run_chatwoot_bridge import RunChatwootRasaBridgeUseCase
from src.infrastructure.chatwoot_bridge.uvicorn_server import UvicornWebhookBridgeServer
from src.shared import config
from src.shared.logger import get_logger

logger = get_logger(__name__)


class ChatwootRasaBridgeController:
    def __init__(self, server: WebhookBridgeServer | None = None):
        self.server = server or UvicornWebhookBridgeServer()
        self.usecase = RunChatwootRasaBridgeUseCase(self.server)

    def run(self) -> int:
        logger.info("Starting Chatwoot-Rasa bridge")
        return self.usecase.execute(config.BRIDGE_HOST, config.PORT, config.RELOAD)
