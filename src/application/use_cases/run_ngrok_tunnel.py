from src.application.ports.ngrok_tunnel import NgrokTunnel
from src.shared.logger import get_logger

logger = get_logger(__name__)


class RunNgrokTunnelUseCase:
    def __init__(self, tunnel: NgrokTunnel):
        self.tunnel = tunnel

    def execute(self) -> int:
        try:
            logger.info("Closing existing ngrok session if any")
            self.tunnel.stop()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to stop previous ngrok session", error=str(exc))
        return self.tunnel.start()
