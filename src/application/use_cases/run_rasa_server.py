from src.application.ports.rasa_runner import RasaRunner


class RunRasaServerUseCase:
    def __init__(self, runner: RasaRunner):
        self.runner = runner

    def execute(self) -> int:
        return self.runner.run_server()
