from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.infrastructure.chatwoot_bridge.uvicorn_server import UvicornWebhookBridgeServer
from src.infrastructure.ngrok.ngrok_cli import NgrokCliTunnel
from src.infrastructure.rasa import rasa_runner
from src.infrastructure.rasa.intent_coverage_parser import (
    RasaIntentCoverageParser,
    _extract_confidence,
    _extract_intent_name,
)
from src.interface_adapter.controllers.chatwoot_rasa_bridge_controller import (
    ChatwootRasaBridgeController,
)
from src.interface_adapter.controllers.ngrok_tunnel_controller import NgrokTunnelController
from src.interface_adapter.controllers.rasa_server_controller import RasaServerController
from src.interface_adapter.controllers.rasa_train_controller import RasaTrainController
from src.interface_adapter.presenters.intent_coverage_presenter import format_intent_coverage
from src.use_cases.intent_coverage_report import (
    ConversationSummary,
    IntentCoverageReport,
    IntentSample,
    TrainingIntentCoverage,
)
from src.use_cases.run_chatwoot_bridge import RunChatwootRasaBridgeUseCase
from src.use_cases.run_ngrok_tunnel import RunNgrokTunnelUseCase
from src.use_cases.run_rasa_server import RunRasaServerUseCase
from src.use_cases.train_rasa_model import TrainRasaModelUseCase


def test_uvicorn_webhook_bridge_server_runs(monkeypatch) -> None:
    called = {}

    def _fake_run(app_import: str, *, host: str, port: int, reload: bool) -> None:
        called["app_import"] = app_import
        called["host"] = host
        called["port"] = port
        called["reload"] = reload

    monkeypatch.setattr("src.infrastructure.chatwoot_bridge.uvicorn_server.uvicorn.run", _fake_run)
    server = UvicornWebhookBridgeServer()
    assert server.run("0.0.0.0", 8080, False) == 0
    assert called["app_import"].endswith("webhook_api:app")
    assert called["host"] == "0.0.0.0"
    assert called["port"] == 8080
    assert called["reload"] is False


def test_ngrok_extract_domain_and_start(monkeypatch) -> None:
    tunnel = NgrokCliTunnel(port=9000, url_webhook="https://demo.example.com/webhook/abc")
    assert tunnel._extract_domain() == "demo.example.com"
    monkeypatch.setattr("src.infrastructure.ngrok.ngrok_cli.subprocess.call", lambda cmd: 7)
    assert tunnel.start() == 7


def test_ngrok_extract_domain_errors() -> None:
    with pytest.raises(RuntimeError):
        NgrokCliTunnel(url_webhook="   ")._extract_domain()
    with pytest.raises(RuntimeError):
        NgrokCliTunnel(url_webhook="https:///")._extract_domain()


def test_ngrok_status_and_stop(monkeypatch) -> None:
    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"tunnels": [{"name": "a"}, {"name": "b"}, {"bad": "skip"}]}

    deleted: list[str] = []
    monkeypatch.setattr("src.infrastructure.ngrok.ngrok_cli.httpx.get", lambda *_args, **_kwargs: _Resp())
    monkeypatch.setattr(
        "src.infrastructure.ngrok.ngrok_cli.httpx.delete",
        lambda url, **_kwargs: deleted.append(url),
    )
    tunnel = NgrokCliTunnel(url_webhook="demo.example.com")
    status = tunnel.status()
    assert status["running"] is True
    tunnel.stop()
    assert len(deleted) == 2


def test_ngrok_status_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.infrastructure.ngrok.ngrok_cli.httpx.get",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("x")),
    )
    tunnel = NgrokCliTunnel(url_webhook="demo.example.com")
    status = tunnel.status()
    assert status["running"] is False
    assert "error" in status


def test_rasa_runner_functions(monkeypatch) -> None:
    assert rasa_runner._extract_port("http://localhost:5006") == "5006"
    assert rasa_runner._extract_port("localhost") == "5005"

    calls: list[tuple[list[str], str]] = []

    def _fake_call(cmd, cwd=None):
        calls.append((cmd, cwd))
        return 0

    monkeypatch.setattr("src.infrastructure.rasa.rasa_runner.subprocess.call", _fake_call)
    monkeypatch.setattr("src.infrastructure.rasa.rasa_runner.config.RASA_BASE_URL", "http://localhost:6000")
    runner = rasa_runner.RasaCliRunner(project_path="/tmp/rasa-project")
    assert runner.run_server() == 0
    assert runner.train() == 0
    assert "--port" in calls[0][0]
    assert calls[0][1] == "/tmp/rasa-project"


def test_rasa_intent_parser_and_extractors(monkeypatch) -> None:
    class _Resp:
        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"intent": {"name": "greet", "confidence": "0.93"}}

    monkeypatch.setattr("src.infrastructure.rasa.intent_coverage_parser.requests.post", lambda *args, **kwargs: _Resp())
    parser = RasaIntentCoverageParser(url="http://rasa/model/parse", timeout=1.5)
    parser.preflight(text="hola")
    prediction = parser.parse_text("hola")
    assert prediction.name == "greet"
    assert prediction.confidence == 0.93
    assert _extract_intent_name({"intent": {"name": "x"}}) == "x"
    assert _extract_intent_name({}) is None
    assert _extract_confidence({"intent": {"confidence": "bad"}}) is None


def test_run_use_cases() -> None:
    bridge_server = SimpleNamespace(run=lambda h, p, r: 11)
    tunnel = SimpleNamespace(stop=lambda: None, start=lambda: 12)
    runner = SimpleNamespace(run_server=lambda: 13, train=lambda: 14)
    assert RunChatwootRasaBridgeUseCase(bridge_server).execute("h", 1, False) == 11
    assert RunNgrokTunnelUseCase(tunnel).execute() == 12
    assert RunRasaServerUseCase(runner).execute() == 13
    assert TrainRasaModelUseCase(runner).execute() == 14


def test_controllers_success_and_errors(monkeypatch, capsys) -> None:
    class _OkUseCase:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def execute(self, *_args, **_kwargs) -> int:
            return 0

    class _FailUseCase(_OkUseCase):
        def execute(self, *_args, **_kwargs) -> int:
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "src.interface_adapter.controllers.chatwoot_rasa_bridge_controller.RunChatwootRasaBridgeUseCase",
        _OkUseCase,
    )
    monkeypatch.setattr(
        "src.interface_adapter.controllers.ngrok_tunnel_controller.RunNgrokTunnelUseCase",
        _FailUseCase,
    )
    monkeypatch.setattr(
        "src.interface_adapter.controllers.rasa_server_controller.RunRasaServerUseCase",
        _FailUseCase,
    )
    monkeypatch.setattr(
        "src.interface_adapter.controllers.rasa_train_controller.TrainRasaModelUseCase",
        _FailUseCase,
    )

    assert ChatwootRasaBridgeController(server=SimpleNamespace()).run() == 0
    assert NgrokTunnelController(tunnel=SimpleNamespace()).run() == 1
    assert RasaServerController(runner=SimpleNamespace()).run() == 1
    assert RasaTrainController(runner=SimpleNamespace()).run() == 1
    err = capsys.readouterr().err
    assert "ERROR: boom" in err


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
