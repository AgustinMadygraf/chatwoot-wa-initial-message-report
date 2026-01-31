from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Message:
    account_id: int
    conversation_id: int
    content: str
    sender_id: Optional[int] = None
    created_at: Optional[datetime] = None
