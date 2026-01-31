"Path: src/application/use_cases/handle_incoming.py"

from datetime import datetime
from typing import Any, Dict

from src.domain.message import Message
from src.application.ports.chatwoot_gateway import ChatwootGateway
from src.application.ports.conversation_store import ConversationStore
from src.application.ports.rasa_gateway import RasaGateway
from src.infrastructure.memory.noop_conversation_store import NoopConversationStore
from src.shared.logger import get_logger

logger = get_logger(__name__)


class HandleIncomingMessageUseCase:
    "Caso de uso para manejar mensajes entrantes de Chatwoot."

    def __init__(
        self,
        gateway: ChatwootGateway,
        store: ConversationStore | None = None,
        rasa: RasaGateway | None = None,
    ):
        self.gateway = gateway
        self.store = store or NoopConversationStore()
        self.rasa = rasa

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        "Maneja un mensaje entrante de Chatwoot y responde usando Rasa si esta configurado."
        event = payload.get("event")
        msg_type = payload.get("message_type")
        if event != "message_created" or msg_type != "incoming":
            return {"ok": True}

        account_id = (payload.get("account") or {}).get("id")
        conversation_id = (payload.get("conversation") or {}).get("id")
        content_in = payload.get("content")
        sender_id = (payload.get("sender") or {}).get("id") if payload.get("sender") else None

        if not account_id or not conversation_id:
            logger.warning("Missing account_id or conversation_id in payload")
            return {"ok": False, "error": "missing account_id or conversation_id"}
        if content_in:
            try:
                await self.store.append_message(
                    Message(
                        account_id=account_id,
                        conversation_id=conversation_id,
                        content=str(content_in),
                        sender_id=sender_id,
                        created_at=datetime.utcnow(),
                    )
                )
            except (ValueError, TypeError, RuntimeError):
                logger.exception("Failed to append incoming message to conversation store")

        content = "Ok"
        fallback_used = False
        if self.rasa and content_in:
            try:
                responses = await self.rasa.send_message(str(conversation_id), str(content_in))
                if responses:
                    content = responses[0]
                else:
                    content = "Bot no activado"
                    fallback_used = True
            except (ValueError, RuntimeError, TimeoutError):
                logger.exception("Error getting response from Rasa, falling back to default content")
                content = "Bot no activado"
                fallback_used = True
        logger.info(
            "Sending reply content to account",
            content=content,
            account_id=account_id,
            conversation_id=conversation_id,
        )

        try:
            status, text = await self.gateway.send_message(account_id, conversation_id, content)
        except (ValueError, RuntimeError, TimeoutError) as exc:
            logger.exception("Error sending message via gateway: %s", exc)
            return {"ok": False, "error": "request error", "detail": str(exc)}

        logger.info("Chatwoot response status", status=status)
        if content and not fallback_used:
            try:
                await self.store.append_message(
                    Message(
                        account_id=account_id,
                        conversation_id=conversation_id,
                        content=str(content),
                        sender_id=None,
                        created_at=datetime.utcnow(),
                    )
                )
            except (ValueError, TypeError, RuntimeError):
                logger.exception("Failed to append outgoing message to conversation store")

        return {"ok": status < 400, "status": status, "detail": text}
