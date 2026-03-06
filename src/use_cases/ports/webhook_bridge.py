from typing import Protocol


class WebhookBridgeServer(Protocol):
    def run(self, host: str, port: int, reload: bool) -> int:
        ...


class PortAvailabilityChecker(Protocol):
    def is_available(self, host: str, port: int) -> bool:
        ...
