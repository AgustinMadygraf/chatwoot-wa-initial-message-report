"""Simple console logger with levels."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Logger:
    name: str = "app"
    level: str = "INFO"

    def _emit(self, level: str, message: str) -> None:
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if levels.index(level) < levels.index(self.level):
            return
        ts = datetime.utcnow().isoformat(timespec="seconds")
        print(f"[{ts}] {self.name} {level}: {message}")

    def debug(self, message: str) -> None:
        self._emit("DEBUG", message)

    def info(self, message: str) -> None:
        self._emit("INFO", message)

    def warning(self, message: str) -> None:
        self._emit("WARNING", message)

    def error(self, message: str) -> None:
        self._emit("ERROR", message)


def get_logger(name: str = "app", level: str | None = None) -> Logger:
    return Logger(name=name, level=(level or "INFO").upper())
