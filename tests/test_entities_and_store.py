import pytest

from src.domain.conversation_memory import ConversationMemory
from src.domain.message import Message
from src.infrastructure.memory.noop_conversation_store import NoopConversationStore


def test_conversation_memory_starts_empty():
    memory = ConversationMemory(account_id=1, conversation_id=2)
    assert memory.messages == []


@pytest.mark.anyio
async def test_noop_store_returns_empty():
    store = NoopConversationStore()
    await store.append_message(Message(1, 2, "hi"))
    history = await store.get_history(1, 2)
    assert history == []
