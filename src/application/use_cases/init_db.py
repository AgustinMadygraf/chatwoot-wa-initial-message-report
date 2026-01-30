from __future__ import annotations

from dataclasses import dataclass

from application.ports.mysql_admin import MySQLAdminPort
from entities.mysql_config import MySQLConfig
from shared.logger import Logger, get_logger


@dataclass(frozen=True)
class InitDbResult:
    ok: bool
    error: str | None = None


def run_init_db(
    config: MySQLConfig,
    admin: MySQLAdminPort,
    logger: Logger | None = None,
) -> InitDbResult:
    logger = logger or get_logger("init-db")
    logger.info("Inicializando base de datos MySQL...")
    try:
        admin.create_database(config)
        admin.check_connection(config)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Init DB fallo: {exc}")
        return InitDbResult(ok=False, error=str(exc))
    logger.info("MySQL listo.")
    return InitDbResult(ok=True)
