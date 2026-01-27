import re
from typing import Dict, List, Pattern, Tuple

# Editable regex catalog for categorization.
# Use ASCII-only by escaping accented characters.
CATEGORIES: List[Tuple[str, Pattern[str]]] = [
    (
        "saludo",
        re.compile(
            r"\b(hola|buen(?:as|os)?\s*(d(?:i|\u00ed)a|tardes|noches)|hi|hello)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "precio",
        re.compile(r"\b(precio|cuesta|vale|costo|coste)\b", re.IGNORECASE),
    ),
    (
        "cotizacion",
        re.compile(
            r"\b(cotizaci(?:o|\u00f3)n|presupuesto|quote)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "estado_pedido",
        re.compile(
            r"\b(estado\s+(del\s+)?pedido|seguimiento|tracking|donde\s+esta\s+mi\s+pedido)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reclamo",
        re.compile(
            r"\b(reclamo|queja|problema|no\s+funciona|defectuoso)\b",
            re.IGNORECASE,
        ),
    ),
]


def categorize_text(text: str) -> str:
    for name, pattern in CATEGORIES:
        if pattern.search(text):
            return name
    return "otro"


__all__ = ["CATEGORIES", "categorize_text"]
