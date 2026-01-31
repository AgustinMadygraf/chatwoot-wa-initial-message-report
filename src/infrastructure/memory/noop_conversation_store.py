from typing import Sequence

from src.domain.message import Message
from src.application.ports.conversation_store import ConversationStore


class NoopConversationStore(ConversationStore):
    async def append_message(self, message: Message) -> None:
        return None

    async def get_history(self, account_id: int, conversation_id: int) -> Sequence[Message]:
        return []
