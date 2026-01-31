from __future__ import annotations

import argparse
import sys
from application.use_cases.intent_coverage_report import IntentCoverageReportUseCase
from infrastructure.pymysql.messages_repository import MessagesRepository
from infrastructure.pymysql.unit_of_work import PyMySQLUnitOfWork
from infrastructure.rasa.intent_coverage_parser import RasaIntentCoverageParser
from infrastructure.rasa.nlu_loader import load_nlu_intents
from interface_adapter.presenter.intent_coverage_presenter import format_intent_coverage
from shared.config import build_mysql_config, get_env, load_env_file
from shared.logger import get_logger


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera un reporte de cobertura de intenciones usando Rasa y MySQL.")
    parser.add_argument("--debug", action="store_true", help="Habilita logs de depuración.")
    parser.add_argument("--min-count", type=int, help="Cantidad mínima para marcar una intención como cubierta.")
    parser.add_argument("--parse-url", type=str, help="URL para `/model/parse` (default: env o RASA_BASE_URL).")
    parser.add_argument("--nlu-file", type=str, help="Ruta al archivo nlu.yml que define las intenciones.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout en segundos para el parseo a Rasa.")
    parser.add_argument("--limit", type=int, default=None, help="Procesar sólo los primeros N mensajes (útil para prueba).")
    parser.add_argument("--samples", type=int, default=0, help="Cuántas predicciones mostrar como ejemplos al final.")
    return parser.parse_args()


def _int_env(name: str, default: int, logger) -> int:
    raw = get_env(name)
    if raw is None:
        return default
    try:
        return max(int(raw), 0)
    except ValueError:
        logger.warning("Valor inválido en env var", var=name, value=raw, default=default)
        return default


def main() -> None:
    load_env_file()
    args = _get_args()
    logger = get_logger("intent-coverage-cli", level="DEBUG" if args.debug else "INFO")

    try:
        nlu_intents = load_nlu_intents(args.nlu_file)
    except Exception as exc:  # noqa: BLE001
        print(f"Fallo al cargar las intenciones de Rasa: {exc}", file=sys.stderr)
        sys.exit(1)

    min_count = args.min_count if args.min_count is not None else _int_env("INTENT_MIN_COUNT", 5, logger)
    scan_every = _int_env("INTENT_SCAN_PROGRESS_EVERY", 5000, logger)
    progress_every = _int_env("INTENT_PROGRESS_EVERY", 200, logger)

    try:
        mysql_config = build_mysql_config()
    except ValueError as exc:
        print(f"Fallo al cargar configuración MySQL: {exc}", file=sys.stderr)
        sys.exit(1)

    parser = RasaIntentCoverageParser(url=args.parse_url, timeout=args.timeout, logger=logger)
    use_case = IntentCoverageReportUseCase(
        parser,
        nlu_intents,
        min_count=min_count,
        progress_every=progress_every,
        scan_progress_every=scan_every,
        sample_limit=args.samples or 0,
        logger=logger,
    )

    with PyMySQLUnitOfWork(mysql_config) as uow:
        repo = MessagesRepository(uow.connection)
        repo.ensure_table()
        rows = list(repo.list_messages(limit=args.limit))

    report = use_case.execute((row.get("content") for row in rows))
    print(format_intent_coverage(report, min_count))
