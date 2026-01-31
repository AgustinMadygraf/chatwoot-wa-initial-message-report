import sys

from src.application.ports.ngrok_tunnel import NgrokTunnel
from src.application.use_cases.run_ngrok_tunnel import RunNgrokTunnelUseCase
from src.infrastructure.ngrok.ngrok_cli import NgrokCliTunnel
from src.shared.logger import get_logger

logger = get_logger(__name__)


class NgrokTunnelController:
    def __init__(self, tunnel: NgrokTunnel | None = None):
        self.tunnel = tunnel or NgrokCliTunnel()
        self.usecase = RunNgrokTunnelUseCase(self.tunnel)

    def run(self) -> int:
        logger.info("Starting ngrok tunnel")
        try:
            return self.usecase.execute()
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
