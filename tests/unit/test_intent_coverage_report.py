from __future__ import annotations

from typing import Iterable

from application.ports.intent_coverage import IntentCoverageParserPort, IntentPrediction
from application.use_cases.intent_coverage_report import IntentCoverageReportUseCase
from infrastructure.rasa.nlu_loader import load_nlu_intents


class _StubParser(IntentCoverageParserPort):
    def __init__(self, mapping: dict[str, IntentPrediction]) -> None:
        self._mapping = mapping

    def parse_text(self, text: str) -> IntentPrediction:
        return self._mapping.get(text, IntentPrediction(name=None))


def test_intent_coverage_counts() -> None:
    parser = _StubParser(
        {
            "hola": IntentPrediction(name="saludo"),
            "adios": IntentPrediction(name="despedida"),
            "otra": IntentPrediction(name="sorpresa"),
            "sin_intent": IntentPrediction(name=None),
        }
    )
    use_case = IntentCoverageReportUseCase(
        parser,
        training_intents=("saludo", "despedida"),
        min_count=2,
        progress_every=1,
        scan_progress_every=1,
    )
    messages = ["hola", "adios", "hola", "sin_intent", "otra", "", None]
    report = use_case.execute(messages)

    assert report.total_rows == 7
    assert report.messages_with_text == 5
    assert report.messages_without_text == 2
    assert report.parse_failures == 0
    assert report.named_predictions == 4
    assert report.fallback_predictions == 1
    assert report.training_coverage[0].intent == "saludo"
    assert report.training_coverage[0].observed_count == 2
    assert report.training_coverage[0].meets_threshold is True
    assert report.training_coverage[1].intent == "despedida"
    assert report.training_coverage[1].observed_count == 1
    assert report.training_coverage[1].meets_threshold is False
    assert report.unknown_intents == (("sorpresa", 1),)


def test_samples_limit_is_respected() -> None:
    parser = _StubParser(
        {
            "hola": IntentPrediction(name="saludo", confidence=0.9),
            "fallback": IntentPrediction(name=None),
            "otro": IntentPrediction(name="start", confidence=0.2),
        }
    )
    use_case = IntentCoverageReportUseCase(
        parser,
        training_intents=("saludo", "despedida", "start"),
        sample_limit=2,
        progress_every=1,
        scan_progress_every=1,
    )
    messages = ["hola", "fallback", "otro"]
    report = use_case.execute(messages)

    assert len(report.samples) == 2
    assert report.samples[0].text == "hola"
    assert report.samples[0].intent == "saludo"
    assert report.samples[0].confidence == 0.9
    assert report.samples[0].is_fallback is False
    assert report.samples[1].text == "fallback"
    assert report.samples[1].intent is None
    assert report.samples[1].is_fallback is True


def test_load_nlu_intents(tmp_path) -> None:
    content = """
version: "3.1"
nlu:
  - intent: saludo
    examples: |
      - hola
  - intent: despedida
  - intent: saludo
  - intent: 
    examples: |
      - 
"""
    path = tmp_path / "nlu.yml"
    path.write_text(content, encoding="utf-8")
    intents = load_nlu_intents(path)

    assert intents == ("saludo", "despedida")
