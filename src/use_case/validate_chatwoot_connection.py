from src.entities.chatwoot_connection_result import ChatwootConnectionResult
from src.use_case.gateways.chatwoot_api_gateway import ChatwootApiGateway


class ValidateChatwootConnectionUseCase:
    def __init__(self, gateway: ChatwootApiGateway) -> None:
        self._gateway = gateway

    def execute(self) -> ChatwootConnectionResult:
        return self._gateway.validate_connection()
