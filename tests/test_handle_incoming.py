import pytest

from src.domain.message import Message
from src.infrastructure.memory.in_memory_conversation_store import InMemoryConversationStore
from src.infrastructure.memory.noop_conversation_store import NoopConversationStore
from src.application.use_cases.handle_incoming import HandleIncomingMessageUseCase


class DummyGateway:
    def __init__(self, status=200, text="ok"):
        self.status = status
        self.text = text
        self.sent = []

    async def send_message(self, account_id, conversation_id, content):
        self.sent.append((account_id, conversation_id, content))
        return self.status, self.text


class DummyRasa:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def send_message(self, sender_id, text):
        self.calls.append((sender_id, text))
        return self.responses


class SpyStore(NoopConversationStore):
    def __init__(self):
        self.messages = []
        self.raise_on_append = False

    async def append_message(self, message: Message) -> None:
        if self.raise_on_append:
            raise RuntimeError("store down")
        self.messages.append(message)


@pytest.mark.anyio
async def test_handle_incoming_ignores_non_incoming():
    usecase = HandleIncomingMessageUseCase(DummyGateway())
    payload = {"event": "conversation_status_changed", "message_type": "incoming"}
    result = await usecase.execute(payload)
    assert result == {"ok": True}


@pytest.mark.anyio
async def test_handle_incoming_missing_ids():
    usecase = HandleIncomingMessageUseCase(DummyGateway())
    payload = {"event": "message_created", "message_type": "incoming"}
    result = await usecase.execute(payload)
    assert result["ok"] is False
    assert result["error"] == "missing account_id or conversation_id"


@pytest.mark.anyio
async def test_handle_incoming_sends_and_stores_message():
    gateway = DummyGateway(status=201, text="created")
    store = SpyStore()
    usecase = HandleIncomingMessageUseCase(gateway, store=store)
    payload = {
        "event": "message_created",
        "message_type": "incoming",
        "account": {"id": 10},
        "conversation": {"id": 20},
        "content": "hola",
        "sender": {"id": 99},
    }
    result = await usecase.execute(payload)
    assert result["ok"] is True
    assert result["status"] == 201
    assert gateway.sent == [(10, 20, "Ok")]
    assert len(store.messages) == 2
    incoming = store.messages[0]
    outgoing = store.messages[1]
    assert incoming.account_id == 10
    assert incoming.conversation_id == 20
    assert incoming.content == "hola"
    assert incoming.sender_id == 99
    assert outgoing.content == "Ok"


@pytest.mark.anyio
async def test_handle_incoming_store_failure_does_not_break():
    gateway = DummyGateway(status=200, text="ok")
    store = SpyStore()
    store.raise_on_append = True
    usecase = HandleIncomingMessageUseCase(gateway, store=store)
    payload = {
        "event": "message_created",
        "message_type": "incoming",
        "account": {"id": 1},
        "conversation": {"id": 2},
        "content": "hola",
    }
    result = await usecase.execute(payload)
    assert result["ok"] is True


@pytest.mark.anyio
async def test_handle_incoming_uses_rasa_response():
    gateway = DummyGateway(status=200, text="ok")
    rasa = DummyRasa(["respuesta"])
    store = SpyStore()
    usecase = HandleIncomingMessageUseCase(gateway, store=store, rasa=rasa)
    payload = {
        "event": "message_created",
        "message_type": "incoming",
        "account": {"id": 1},
        "conversation": {"id": 2},
        "content": "hola",
    }
    result = await usecase.execute(payload)
    assert result["ok"] is True
    assert gateway.sent == [(1, 2, "respuesta")]
    assert rasa.calls == [("2", "hola")]


@pytest.mark.anyio
async def test_in_memory_store_maxlen():
    store = InMemoryConversationStore(max_messages=2)
    await store.append_message(Message(1, 1, "a"))
    await store.append_message(Message(1, 1, "b"))
    await store.append_message(Message(1, 1, "c"))
    history = await store.get_history(1, 1)
    assert [m.content for m in history] == ["b", "c"]
