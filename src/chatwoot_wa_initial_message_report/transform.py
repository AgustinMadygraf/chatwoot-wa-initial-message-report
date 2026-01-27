import re

from .categories import categorize_text


def normalize_literal(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def categorize(text: str) -> str:
    return categorize_text(text)
