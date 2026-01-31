from src.application.ports.rasa_runner import RasaRunner


class TrainRasaModelUseCase:
    def __init__(self, runner: RasaRunner):
        self.runner = runner

    def execute(self) -> int:
        return self.runner.train()
