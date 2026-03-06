from src.use_cases.ports.webhook_bridge import WebhookBridgeServer
from src.use_cases.run_chatwoot_bridge import RunChatwootRasaBridgeUseCase
from src.infrastructure.uvicorn.webhook_bridge_server import UvicornWebhookBridgeServer
from src.infrastructure.settings import config
from src.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ChatwootRasaBridgeController:
    def __init__(self, server: WebhookBridgeServer | None = None):
        self.server = server or UvicornWebhookBridgeServer()
        self.usecase = RunChatwootRasaBridgeUseCase(self.server)

    def run(self) -> int:
        logger.info("Starting Chatwoot-Rasa bridge")
        return self.usecase.execute(config.BRIDGE_HOST, config.PORT, config.RELOAD)
