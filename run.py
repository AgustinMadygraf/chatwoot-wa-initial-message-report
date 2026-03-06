import sys

from src.infrastructure.requests.chatwoot_requests_gateway import ChatwootRequestsGateway
from src.infrastructure.settings.env_settings import load_chatwoot_settings
from src.interface_adapter.controllers.validate_connection_controller import (
    ValidateConnectionController,
)
from src.interface_adapter.presenters.console_presenter import ConsoleConnectionPresenter
from src.use_case.validate_chatwoot_connection import ValidateChatwootConnectionUseCase


def main() -> int:
    settings = load_chatwoot_settings()
    gateway = ChatwootRequestsGateway(settings=settings)
    use_case = ValidateChatwootConnectionUseCase(gateway=gateway)
    presenter = ConsoleConnectionPresenter()
    controller = ValidateConnectionController(use_case=use_case, presenter=presenter)
    return controller.run()


if __name__ == "__main__":
    raise SystemExit(main())
