from src.application.ports.webhook_bridge import WebhookBridgeServer


class RunChatwootRasaBridgeUseCase:
    def __init__(self, server: WebhookBridgeServer):
        self.server = server

    def execute(self, host: str, port: int, reload: bool) -> int:
        return self.server.run(host, port, reload)
