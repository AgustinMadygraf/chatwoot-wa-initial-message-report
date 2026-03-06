from typing import Protocol, Sequence


class RasaGateway(Protocol):
    async def send_message(self, sender_id: str, text: str) -> Sequence[str]:
        ...
