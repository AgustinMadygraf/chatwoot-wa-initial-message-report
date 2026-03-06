from src.entities.chatwoot_contacts_result import ChatwootContactsResult
from src.use_case.gateways.chatwoot_api_gateway import ChatwootApiGateway


class FetchChatwootContactsUseCase:
    def __init__(self, gateway: ChatwootApiGateway) -> None:
        self._gateway = gateway

    def execute(self) -> ChatwootContactsResult:
        return self._gateway.fetch_contacts_page()
