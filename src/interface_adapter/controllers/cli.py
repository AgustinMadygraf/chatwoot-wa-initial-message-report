from __future__ import annotations

import argparse
import json

from src.shared.config import load_env_file
from src.shared.logger import get_logger
from src.use_cases.health_check import run_health_checks


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica conectividad con Chatwoot API y MySQL.")
    parser.add_argument("--json", action="store_true", help="Imprime salida en JSON.")
    return parser.parse_args()


def main() -> None:
    load_env_file()
    args = _get_args()
    logger = get_logger("cli")
    results = run_health_checks(logger=logger)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    print("Estado general:", "OK" if results["ok"] else "ERROR")
    for key in ("chatwoot", "mysql"):
        item = results[key]
        status = "OK" if item["ok"] else "ERROR"
        detail = f" - {item.get('error')}" if item.get("error") else ""
        print(f"{key}: {status}{detail}")
