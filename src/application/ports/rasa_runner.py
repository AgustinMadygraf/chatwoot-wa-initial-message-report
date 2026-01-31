from typing import Protocol


class RasaRunner(Protocol):
    def run_server(self) -> int:
        ...

    def train(self) -> int:
        ...
