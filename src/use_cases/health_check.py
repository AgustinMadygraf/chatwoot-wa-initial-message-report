from __future__ import annotations

from use_cases.ports.health_check import HealthCheckPort, HealthCheckResults
from infrastructure.logging.logger import Logger, get_logger


def run_health_checks(
    checker: HealthCheckPort,
    logger: Logger | None = None,
) -> HealthCheckResults:
    logger = logger or get_logger("health")
    results = checker.check()
    results["ok"] = bool(results["chatwoot"]["ok"] and results["mysql"]["ok"])
    logger.info("Health check ejecutado.")
    return results
