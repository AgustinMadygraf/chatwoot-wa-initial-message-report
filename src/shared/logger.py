"""Logging helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime


def _emit_json(entry: dict[str, str | dict]) -> None:
    print(json.dumps(entry))


@dataclass
class Logger:
    name: str = "app"
    level: str = "INFO"
    fmt: str = os.getenv("LOG_FORMAT", "text")

    def _emit(self, level: str, message: str, **extras: dict) -> None:
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if levels.index(level) < levels.index(self.level):
            return
        ts = datetime.utcnow().isoformat(timespec="seconds")
        entry = {
            "timestamp": ts,
            "logger": self.name,
            "level": level,
            "message": message,
        }
        entry.update(extras)
        if self.fmt == "json":
            _emit_json(entry)
        else:
            extras_text = ""
            if extras:
                pairs = " ".join(f"{key}={value}" for key, value in extras.items())
                extras_text = f" | {pairs}"
            print(f"[{ts}] {self.name} {level}: {message}{extras_text}")

    def debug(self, message: str, **extras: dict) -> None:
        self._emit("DEBUG", message, **extras)

    def info(self, message: str, **extras: dict) -> None:
        self._emit("INFO", message, **extras)

    def warning(self, message: str, **extras: dict) -> None:
        self._emit("WARNING", message, **extras)

    def error(self, message: str, **extras: dict) -> None:
        self._emit("ERROR", message, **extras)


def get_logger(name: str = "app", level: str | None = None) -> Logger:
    return Logger(name=name, level=(level or "INFO").upper())
