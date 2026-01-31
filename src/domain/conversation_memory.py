from dataclasses import dataclass, field
from typing import List

from src.domain.message import Message


@dataclass
class ConversationMemory:
    account_id: int
    conversation_id: int
    messages: List[Message] = field(default_factory=list)
