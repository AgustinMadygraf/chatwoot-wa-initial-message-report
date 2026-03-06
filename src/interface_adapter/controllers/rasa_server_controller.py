import sys

from src.use_cases.ports.rasa_runner import RasaRunner
from src.use_cases.run_rasa_server import RunRasaServerUseCase
from src.infrastructure.rasa.rasa_runner import RasaCliRunner
from src.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class RasaServerController:
    def __init__(self, runner: RasaRunner | None = None):
        self.runner = runner or RasaCliRunner()
        self.usecase = RunRasaServerUseCase(self.runner)

    def run(self) -> int:
        logger.info("Starting Rasa server")
        try:
            return self.usecase.execute()
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
