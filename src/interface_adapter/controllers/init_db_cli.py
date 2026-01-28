from __future__ import annotations

import argparse
import sys

from src.entities.mysql_config import MySQLConfig
from src.infrastructure.pymysql.mysql_admin_gateway import PyMySQLAdminGateway
from src.interface_adapter.presenter.init_db_presenter import present_init_db
from src.shared.config import get_env, load_env_file
from src.shared.logger import get_logger
from src.use_cases.init_db import run_init_db


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inicializa la DB MySQL requerida.")
    parser.add_argument("--debug", action="store_true", help="Habilita logs de depuración.")
    return parser.parse_args()


def _require_env(name: str) -> str:
    value = get_env(name)
    if not value:
        raise ValueError(f"Missing env var: {name}")
    return value


def main() -> None:
    load_env_file()
    args = _get_args()
    logger = get_logger("init-db-cli", level="DEBUG" if args.debug else "INFO")

    try:
        config = MySQLConfig(
            host=_require_env("MYSQL_HOST"),
            user=_require_env("MYSQL_USER"),
            password=_require_env("MYSQL_PASSWORD"),
            database=_require_env("MYSQL_DB"),
            port=int(get_env("MYSQL_PORT", "3306")),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Init DB fallo: {exc}")
        sys.exit(1)

    result = run_init_db(config, PyMySQLAdminGateway(), logger=logger)
    print(present_init_db(result))
    if not result.ok:
        sys.exit(1)
