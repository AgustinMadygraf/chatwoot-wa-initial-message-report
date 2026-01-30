from __future__ import annotations

from pathlib import Path

from shared.config import load_env_file


def test_load_env_file_missing_is_noop(tmp_path: Path) -> None:
    missing = tmp_path / "missing.env"
    load_env_file(str(missing))
