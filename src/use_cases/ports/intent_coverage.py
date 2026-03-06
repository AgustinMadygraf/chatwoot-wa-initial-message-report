from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class IntentPrediction:
    """Represents the intent that Rasa inferred for a text snippet."""

    name: str | None
    confidence: float | None = None


class IntentCoverageParserPort(Protocol):
    """Contract for a component that can parse text through Rasa."""

    def parse_text(self, text: str) -> IntentPrediction:
        """Return the prediction for `text`. Exceptions propagate for callers to handle."""
        ...
