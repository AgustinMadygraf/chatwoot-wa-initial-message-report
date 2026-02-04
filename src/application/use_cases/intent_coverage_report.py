from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from application.dto.message_snapshot import MessageSnapshot
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
class ConversationSummary:
    """Aggregated view per conversation."""

    conversation_id: int | None
    total_messages: int
    fallback_count: int
    fallback_pct: float
    top_intent: str | None
    top_intent_count: int
    last_text: str
    last_confidence: float | None
    last_activity: int | None


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
    conversations: tuple[ConversationSummary, ...]


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

    def execute(self, messages: Iterable[MessageSnapshot]) -> IntentCoverageReport:
        ordered_messages = self._order_messages_by_conversation(messages)
        total_rows = 0
        messages_with_text = 0
        messages_without_text = 0
        parse_failures = 0
        named_predictions = 0
        fallback_predictions = 0
        counter: Counter[str] = Counter()
        samples: list[IntentSample] = []
        conversation_stats: dict[int | None, dict[str, Any]] = {}

        for message in ordered_messages:
            total_rows += 1
            text = message.content.strip()
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

            conversation_id = message.conversation_id
            stats = conversation_stats.setdefault(
                conversation_id,
                {
                    "counter": Counter(),
                    "fallback": 0,
                    "total": 0,
                    "last_text": text,
                    "last_confidence": prediction.confidence,
                    "last_activity": message.created_at,
                },
            )
            stats["total"] += 1
            stats["last_text"] = text
            stats["last_confidence"] = prediction.confidence
            stats["last_activity"] = _max_int(stats["last_activity"], message.created_at)
            if prediction.name:
                stats["counter"][prediction.name] += 1
            else:
                stats["fallback"] += 1

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

        conversation_summaries = self._build_conversation_summaries(conversation_stats)

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
            conversations=tuple(conversation_summaries),
        )

    def _order_messages_by_conversation(
        self, messages: Iterable[MessageSnapshot]
    ) -> list[MessageSnapshot]:
        grouped: dict[int | None, list[MessageSnapshot]] = {}
        last_activity: dict[int | None, int] = {}

        for message in messages:
            group = grouped.setdefault(message.conversation_id, [])
            group.append(message)
            activity = _safe_int(message.created_at)
            current = last_activity.get(message.conversation_id, 0)
            if activity > current:
                last_activity[message.conversation_id] = activity

        def convo_key(item: tuple[int | None, list[MessageSnapshot]]) -> tuple[int, int | None]:
            conv_id, _ = item
            return (last_activity.get(conv_id, 0), conv_id)

        ordered: list[MessageSnapshot] = []
        for conv_id, items in sorted(grouped.items(), key=convo_key):
            items.sort(key=lambda msg: (_safe_int(msg.created_at), msg.conversation_id))
            ordered.extend(items)
        return ordered

    def _build_conversation_summaries(
        self,
        stats: dict[int | None, dict[str, Any]],
    ) -> list[ConversationSummary]:
        summaries: list[ConversationSummary] = []
        for conv_id, info in stats.items():
            total = info["total"]
            fallback = info["fallback"]
            counter: Counter[str] = info["counter"]
            top_intent, top_count = self._top_intent(counter)
            fallback_pct = (fallback / total) * 100 if total else 0.0
            last_text = info["last_text"]
            last_confidence = info["last_confidence"]
            last_activity = info.get("last_activity")
            summaries.append(
                ConversationSummary(
                    conversation_id=conv_id,
                    total_messages=total,
                    fallback_count=fallback,
                    fallback_pct=fallback_pct,
                    top_intent=top_intent,
                    top_intent_count=top_count,
                    last_text=last_text,
                    last_confidence=last_confidence,
                    last_activity=last_activity,
                )
            )
        summaries.sort(key=lambda item: (_safe_int(item.last_activity), item.conversation_id))
        return summaries

    @staticmethod
    def _top_intent(counter: Counter[str]) -> tuple[str | None, int]:
        if not counter:
            return None, 0
        intent, count = counter.most_common(1)[0]
        return intent, count


def _safe_int(value: int | None) -> int:
    return int(value) if value is not None else 0


def _max_int(left: int | None, right: int | None) -> int | None:
    if left is None:
        return right
    if right is None:
        return left
    return max(left, right)
