from __future__ import annotations

from types import SimpleNamespace

from src.infrastructure.uvicorn.webhook_bridge_server import UvicornWebhookBridgeServer
from src.interface_adapter.controllers.chatwoot_bridge_controller import (
    ChatwootBridgeController,
)
from src.interface_adapter.presenters.intent_coverage_presenter import format_intent_coverage
from src.use_cases.intent_coverage_report import (
    ConversationSummary,
    IntentCoverageReport,
    IntentSample,
    TrainingIntentCoverage,
)
from src.use_cases.run_chatwoot_bridge_server import RunChatwootBridgeUseCase


def test_uvicorn_webhook_bridge_server_runs(monkeypatch) -> None:
    called = {}

    def _fake_run(app_import: str, *, host: str, port: int, reload: bool) -> None:
        called["app_import"] = app_import
        called["host"] = host
        called["port"] = port
        called["reload"] = reload

    monkeypatch.setattr("src.infrastructure.uvicorn.webhook_bridge_server.uvicorn.run", _fake_run)
    server = UvicornWebhookBridgeServer()
    assert server.run("0.0.0.0", 8080, False) == 0
    assert called["app_import"].endswith("webhook_api:app")
    assert called["host"] == "0.0.0.0"
    assert called["port"] == 8080
    assert called["reload"] is False


def test_run_use_cases() -> None:
    bridge_server = SimpleNamespace(run=lambda h, p, r: 11)
    assert RunChatwootBridgeUseCase(bridge_server).execute("h", 1, False) == 11


def test_controllers_success_and_errors(monkeypatch, capsys) -> None:
    class _OkUseCase:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def execute(self, *_args, **_kwargs) -> int:
            return 0

    monkeypatch.setattr(
        "src.interface_adapter.controllers.chatwoot_bridge_controller.RunChatwootBridgeUseCase",
        _OkUseCase,
    )

    assert ChatwootBridgeController(server=SimpleNamespace()).run() == 0
    _ = capsys.readouterr()


def test_intent_coverage_presenter_formats_sections() -> None:
    report = IntentCoverageReport(
        total_rows=10,
        messages_with_text=8,
        messages_without_text=2,
        parse_failures=1,
        named_predictions=6,
        fallback_predictions=2,
        training_coverage=(
            TrainingIntentCoverage(intent="saludo", observed_count=4, meets_threshold=True),
            TrainingIntentCoverage(intent="despedida", observed_count=1, meets_threshold=False),
        ),
        unknown_intents=(("otro", 1),),
        samples=(IntentSample(text="hola mundo", intent="saludo", confidence=0.91, is_fallback=False),),
        conversations=(
            ConversationSummary(
                conversation_id=1,
                total_messages=3,
                fallback_count=1,
                fallback_pct=33.3,
                top_intent="saludo",
                top_intent_count=2,
                last_text="hola mundo",
                last_confidence=0.91,
                last_activity=100,
            ),
        ),
    )
    out = format_intent_coverage(report, min_count=2, conversation_limit=1)
    assert "Reporte de cobertura de intenciones" in out
    assert "Intenciones con cobertura baja" in out
    assert "Intenciones inferidas fuera del NLU" in out
    assert "Resumen por conversaciones" in out
