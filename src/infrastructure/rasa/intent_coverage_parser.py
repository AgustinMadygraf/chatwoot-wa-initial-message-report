from __future__ import annotations

from typing import Any

import requests

from application.ports.intent_coverage import IntentCoverageParserPort, IntentPrediction
from shared.config import get_rasa_parse_url
from shared.logger import Logger, get_logger


class RasaIntentCoverageParser(IntentCoverageParserPort):
    """Simple HTTP client that forwards texts to Rasa's `/model/parse` endpoint."""

    def __init__(self, *, url: str | None = None, timeout: float = 10.0, logger: Logger | None = None) -> None:
        self._url = url or get_rasa_parse_url()
        self._timeout = timeout
        self._logger = logger or get_logger("intent-coverage-parser")

    def parse_text(self, text: str) -> IntentPrediction:
        response = requests.post(self._url, json={"text": text}, timeout=self._timeout)
        response.raise_for_status()
        payload = response.json()
        intent_name = _extract_intent_name(payload)
        confidence = _extract_confidence(payload)
        return IntentPrediction(name=intent_name, confidence=confidence)


def _extract_intent_name(payload: dict[str, Any]) -> str | None:
    intent = payload.get("intent")
    if isinstance(intent, dict):
        name = intent.get("name")
        if isinstance(name, str):
            return name
    return None


def _extract_confidence(payload: dict[str, Any]) -> float | None:
    intent = payload.get("intent")
    if isinstance(intent, dict):
        value = intent.get("confidence")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return None
