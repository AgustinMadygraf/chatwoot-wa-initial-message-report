from fastapi import FastAPI, Request

from src.infrastructure.chatwoot_api.chatwoot_http import ChatwootHTTPAdapter
from src.infrastructure.memory.in_memory_conversation_store import InMemoryConversationStore
from src.use_cases.handle_incoming import HandleIncomingMessageUseCase
from src.interface_adapter.controllers.webhook_controller import WebhookController

app = FastAPI()

adapter = ChatwootHTTPAdapter()
store = InMemoryConversationStore()
usecase = HandleIncomingMessageUseCase(adapter, store=store, rasa=None)
controller = WebhookController(usecase)


@app.post("/webhook/{secret}")
async def webhook(secret: str, request: Request):
    return await controller.handle(secret, request)
