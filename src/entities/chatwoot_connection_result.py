from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChatwootConnectionResult:
    ok: bool
    status_code: Optional[int]
    endpoint: str
    detail: str
