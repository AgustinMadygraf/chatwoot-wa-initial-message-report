from src.application.ports.ngrok_tunnel import NgrokTunnel


class RunNgrokTunnelUseCase:
    def __init__(self, tunnel: NgrokTunnel):
        self.tunnel = tunnel

    def execute(self) -> int:
        return self.tunnel.start()
