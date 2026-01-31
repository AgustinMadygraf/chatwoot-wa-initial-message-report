"""Logging helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
import sys


def _emit_json(entry: dict[str, str | dict]) -> None:
    print(json.dumps(entry))


@dataclass
class Logger:
    name: str = "app"
    level: str = "INFO"
    fmt: str = os.getenv("LOG_FORMAT", "text")

    def _format_message(self, message: str, args: tuple[object, ...]) -> str:
        if not args:
            return message
        try:
            return message % args
        except Exception:
            args_text = " ".join(str(arg) for arg in args)
            return f"{message} {args_text}".strip()

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

    def debug(self, message: str, *args: object, **extras: dict) -> None:
        self._emit("DEBUG", self._format_message(message, args), **extras)

    def info(self, message: str, *args: object, **extras: dict) -> None:
        self._emit("INFO", self._format_message(message, args), **extras)

    def warning(self, message: str, *args: object, **extras: dict) -> None:
        self._emit("WARNING", self._format_message(message, args), **extras)

    def error(self, message: str, *args: object, **extras: dict) -> None:
        self._emit("ERROR", self._format_message(message, args), **extras)

    def exception(self, message: str, *args: object, **extras: dict) -> None:
        if not args and "error" not in extras:
            exc = sys.exc_info()[1]
            if exc is not None:
                extras["error"] = str(exc)
        self._emit("ERROR", self._format_message(message, args), **extras)


def get_logger(name: str = "app", level: str | None = None) -> Logger:
    return Logger(name=name, level=(level or "INFO").upper())
