import sys

from src.application.ports.rasa_runner import RasaRunner
from src.application.use_cases.train_rasa_model import TrainRasaModelUseCase
from src.infrastructure.rasa.rasa_runner import RasaCliRunner
from src.shared.logger import get_logger

logger = get_logger(__name__)


class RasaTrainController:
    def __init__(self, runner: RasaRunner | None = None):
        self.runner = runner or RasaCliRunner()
        self.usecase = TrainRasaModelUseCase(self.runner)

    def run(self) -> int:
        logger.info("Training Rasa model")
        try:
            return self.usecase.execute()
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
