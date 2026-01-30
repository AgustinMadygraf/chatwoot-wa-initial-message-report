from __future__ import annotations

from dataclasses import dataclass

from src.entities.mysql_config import MySQLConfig
from src.interface_adapter.gateways.mysql_admin_gateway import MySQLAdminGateway
from src.shared.logger import Logger, get_logger


@dataclass(frozen=True)
class InitDbResult:
    ok: bool
    error: str | None = None


def run_init_db(
    config: MySQLConfig,
    gateway: MySQLAdminGateway,
    logger: Logger | None = None,
) -> InitDbResult:
    logger = logger or get_logger("init-db")
    logger.info("Inicializando base de datos MySQL...")
    try:
        gateway.create_database(config)
        gateway.check_connection(config)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Init DB fallo: {exc}")
        return InitDbResult(ok=False, error=str(exc))
    logger.info("MySQL listo.")
    return InitDbResult(ok=True)
