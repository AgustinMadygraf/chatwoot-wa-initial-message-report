import sys

from src.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class RasaServerController:
    def __init__(self, runner=None):
        self.runner = runner

    def run(self) -> int:
        logger.warning("Rasa integration is disabled in this repository")
        print("ERROR: Rasa integration is disabled", file=sys.stderr)
        return 1
