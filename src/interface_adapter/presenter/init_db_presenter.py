from __future__ import annotations

from use_cases.init_db import InitDbResult


def present_init_db(result: InitDbResult) -> str:
    if result.ok:
        return "MySQL listo. DB verificada."
    return f"Init DB fallo: {result.error}"
