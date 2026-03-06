from src.use_cases.ports.webhook_bridge import PortAvailabilityChecker, WebhookBridgeServer


class RunChatwootBridgeUseCase:
    def __init__(self, server: WebhookBridgeServer, checker: PortAvailabilityChecker):
        self.server = server
        self.checker = checker

    def execute(self, host: str, port: int, reload: bool) -> int:
        for candidate_port in range(port, 65536):
            if self.checker.is_available(host, candidate_port):
                return self.server.run(host, candidate_port, reload)
        raise RuntimeError(f"No available ports found from {port} to 65535")
