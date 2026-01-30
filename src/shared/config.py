"""Shared configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ChatwootConfig:
    base_url: str
    account_id: str
    api_token: str
    inbox_id: str
    days: int | None = None
    since: str | None = None
    data_dir: str = "data"


def load_env_file(path: str = ".env") -> None:
    """Load simple KEY=VALUE pairs from a .env file into the process env.

    Existing environment variables are not overwritten.
    """
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)
