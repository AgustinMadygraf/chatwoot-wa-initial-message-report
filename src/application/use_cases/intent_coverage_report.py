from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from application.ports.intent_coverage import IntentCoverageParserPort
from shared.logger import Logger, get_logger


@dataclass(frozen=True)
class TrainingIntentCoverage:
    """Summary for a single intent defined in the training data."""

    intent: str
    observed_count: int
    meets_threshold: bool


@dataclass(frozen=True)
class IntentSample:
    """Representative prediction captured for diagnostics."""

    text: str
    intent: str | None
    confidence: float | None
    is_fallback: bool


@dataclass(frozen=True)
class IntentCoverageReport:
    """Final shape produced by the intent coverage use case."""

    total_rows: int
    messages_with_text: int
    messages_without_text: int
    parse_failures: int
    named_predictions: int
    fallback_predictions: int
    training_coverage: tuple[TrainingIntentCoverage, ...]
    unknown_intents: tuple[tuple[str, int], ...]
    samples: tuple[IntentSample, ...]


class IntentCoverageReportUseCase:
    """Core logic that fetches intent predictions and compares them to training data."""

    def __init__(
        self,
        parser: IntentCoverageParserPort,
        training_intents: Iterable[str],
        *,
        min_count: int = 5,
        progress_every: int = 200,
        scan_progress_every: int = 5000,
        sample_limit: int = 0,
        logger: Logger | None = None,
    ) -> None:
        self._parser = parser
        self._training_intents = tuple(dict.fromkeys(training_intents))
        self._training_set = set(self._training_intents)
        self._min_count = max(min_count, 0)
        self._progress_every = max(progress_every, 0)
        self._scan_progress_every = max(scan_progress_every, 0)
        self._sample_limit = max(sample_limit, 0)
        self._logger = logger or get_logger("intent-coverage")

    def execute(self, messages: Iterable[str | None]) -> IntentCoverageReport:
        total_rows = 0
        messages_with_text = 0
        messages_without_text = 0
        parse_failures = 0
        named_predictions = 0
        fallback_predictions = 0
        counter: Counter[str] = Counter()
        samples: list[IntentSample] = []

        for raw_text in messages:
            total_rows += 1
            text = (raw_text or "").strip()
            if not text:
                messages_without_text += 1
                continue
            messages_with_text += 1
            if self._scan_progress_every and messages_with_text % self._scan_progress_every == 0:
                self._logger.info("Procesando mensajes", processed=messages_with_text)

            try:
                prediction = self._parser.parse_text(text)
            except Exception as exc:  # noqa: BLE001
                parse_failures += 1
                self._logger.warning("Intent coverage parse failed", error=str(exc))
                continue

            sample = IntentSample(
                text=text,
                intent=prediction.name,
                confidence=prediction.confidence,
                is_fallback=not bool(prediction.name),
            )
            if self._sample_limit and len(samples) < self._sample_limit:
                samples.append(sample)

            if not prediction.name:
                fallback_predictions += 1
                continue

            named_predictions += 1
            counter[prediction.name] += 1

            if self._progress_every and named_predictions % self._progress_every == 0:
                self._logger.debug("Predicciones procesadas", total=named_predictions)

        training_coverage = tuple(
            TrainingIntentCoverage(
                intent=intent,
                observed_count=counter.get(intent, 0),
                meets_threshold=counter.get(intent, 0) >= self._min_count,
            )
            for intent in self._training_intents
        )

        unknown_intents = tuple(
            sorted(
                ((intent, count) for intent, count in counter.items() if intent not in self._training_set),
                key=lambda pair: pair[1],
                reverse=True,
            )
        )

        return IntentCoverageReport(
            total_rows=total_rows,
            messages_with_text=messages_with_text,
            messages_without_text=messages_without_text,
            parse_failures=parse_failures,
            named_predictions=named_predictions,
            fallback_predictions=fallback_predictions,
            training_coverage=training_coverage,
            unknown_intents=unknown_intents,
            samples=tuple(samples),
        )
