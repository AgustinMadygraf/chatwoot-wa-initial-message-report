from collections import defaultdict, deque
from typing import Deque, Dict, Sequence, Tuple

from src.domain.message import Message
from src.application.ports.conversation_store import ConversationStore


class InMemoryConversationStore(ConversationStore):
    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self._store: Dict[Tuple[int, int], Deque[Message]] = defaultdict(
            lambda: deque(maxlen=self.max_messages)
        )

    async def append_message(self, message: Message) -> None:
        self._store[(message.account_id, message.conversation_id)].append(message)

    async def get_history(self, account_id: int, conversation_id: int) -> Sequence[Message]:
        return list(self._store.get((account_id, conversation_id), []))
