from typing import Protocol, Sequence

from src.domain.message import Message


class ConversationStore(Protocol):
    async def append_message(self, message: Message) -> None:
        ...

    async def get_history(self, account_id: int, conversation_id: int) -> Sequence[Message]:
        ...
