from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_NLU_FILE = Path(__file__).resolve().parent / "data" / "nlu.yml"


def load_nlu_intents(file_path: str | Path | None = None) -> tuple[str, ...]:
    """Read the Rasa NLU file and return the intents in definition order."""

    target = Path(file_path) if file_path else DEFAULT_NLU_FILE
    if not target.exists():
        raise FileNotFoundError(f"NLU file not found: {target}")

    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    nlu = raw.get("nlu")
    if not isinstance(nlu, list):
        return ()

    intents: list[str] = []
    for block in nlu:
        if not isinstance(block, dict):
            continue
        intent_name = block.get("intent")
        if isinstance(intent_name, str) and intent_name.strip():
            intents.append(intent_name.strip())

    # Preserve first-occurrence order while removing duplicates.
    return tuple(dict.fromkeys(intents))
