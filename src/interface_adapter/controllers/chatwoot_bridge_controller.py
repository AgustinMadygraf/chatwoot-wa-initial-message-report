from src.use_cases.run_chatwoot_bridge_server import RunChatwootBridgeUseCase
from src.infrastructure.settings import config
from src.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ChatwootBridgeController:
    def __init__(self, usecase: RunChatwootBridgeUseCase):
        self.usecase = usecase

    def run(self) -> int:
        logger.info("Starting Chatwoot bridge")
        return self.usecase.execute(config.BRIDGE_HOST, config.PORT, config.RELOAD)
