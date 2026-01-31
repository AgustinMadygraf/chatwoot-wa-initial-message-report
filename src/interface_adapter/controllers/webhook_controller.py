from fastapi import HTTPException, Request

from src.shared import config
from src.shared.logger import get_logger
from src.application.use_cases.handle_incoming import HandleIncomingMessageUseCase

logger = get_logger(__name__)


class WebhookController:
    def __init__(self, usecase: HandleIncomingMessageUseCase):
        self.usecase = usecase

    async def handle(self, secret: str, request: Request):
        if secret != config.WEBHOOK_SECRET:
            logger.warning(
                "Unauthorized webhook attempt",
                secret_length=len(secret or ""),
            )
            raise HTTPException(status_code=401, detail="unauthorized")

        payload = await request.json()
        event = payload.get("event")
        msg_type = payload.get("message_type")
        sender = (payload.get("sender") or {}).get("id") if payload.get("sender") else None
        logger.info(
            "Received webhook",
            event=event,
            message_type=msg_type,
            sender=sender,
        )

        try:
            result = await self.usecase.execute(payload)
        except Exception:
            logger.exception("Unhandled error in usecase")
            raise

        return result
