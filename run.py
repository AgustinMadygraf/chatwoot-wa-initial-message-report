"""
Path: run.py
"""

from src.infrastructure.cli.view import RichCliView
from src.infrastructure.network.socket_port_checker import SocketPortAvailabilityChecker
from src.infrastructure.settings import config
from src.infrastructure.uvicorn.webhook_bridge_server import UvicornWebhookBridgeServer
from src.interface_adapter.controllers.chatwoot_bridge_controller import ChatwootBridgeController
from src.interface_adapter.presenters.cli_app import RuntimeStatus, create_app
from src.use_cases.run_chatwoot_bridge_server import RunChatwootBridgeUseCase


def run_bridge() -> int:
    config.load_env_file()
    usecase = RunChatwootBridgeUseCase(
        server=UvicornWebhookBridgeServer(),
        checker=SocketPortAvailabilityChecker(),
    )
    return ChatwootBridgeController(usecase=usecase).run()


def get_runtime_status() -> RuntimeStatus:
    config.load_env_file()
    return RuntimeStatus(
        host=config.BRIDGE_HOST,
        port=config.PORT,
        reload=config.RELOAD,
        secret_set=bool(config.get_webhook_secret()),
    )


app = create_app(
    run_bridge=run_bridge,
    get_runtime_status=get_runtime_status,
    view=RichCliView(),
)


if __name__ == "__main__":
    app()
