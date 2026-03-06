from src.interface_adapter.presenters.contacts_presenter import ContactsPresenter
from src.use_case.fetch_chatwoot_contacts import FetchChatwootContactsUseCase


class FetchContactsController:
    def __init__(
        self,
        use_case: FetchChatwootContactsUseCase,
        presenter: ContactsPresenter,
    ) -> None:
        self._use_case = use_case
        self._presenter = presenter

    def run(self) -> int:
        result = self._use_case.execute()
        return self._presenter.present(result)
