from typing import Protocol, Tuple


class ChatwootGateway(Protocol):
    async def send_message(self, account_id: int, conversation_id: int, content: str) -> Tuple[int, str]:
        "Send a message to a conversation in Chatwoot."
        ...
