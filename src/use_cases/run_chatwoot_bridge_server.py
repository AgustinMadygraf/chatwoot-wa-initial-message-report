from src.use_cases.ports.webhook_bridge import WebhookBridgeServer


class RunChatwootBridgeUseCase:
    def __init__(self, server: WebhookBridgeServer):
        self.server = server

    def execute(self, host: str, port: int, reload: bool) -> int:
        return self.server.run(host, port, reload)
