from typing import Any, Mapping, Protocol


class NgrokTunnel(Protocol):
    def start(self) -> int:
        ...

    def stop(self) -> None:
        ...

    def status(self) -> Mapping[str, Any]:
        ...
