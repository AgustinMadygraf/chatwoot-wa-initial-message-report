from src.interface_adapter.presenters.connection_presenter import ConnectionPresenter
from src.use_case.validate_chatwoot_connection import ValidateChatwootConnectionUseCase


class ValidateConnectionController:
    def __init__(
        self,
        use_case: ValidateChatwootConnectionUseCase,
        presenter: ConnectionPresenter,
    ) -> None:
        self._use_case = use_case
        self._presenter = presenter

    def run(self) -> int:
        result = self._use_case.execute()
        return self._presenter.present(result)
