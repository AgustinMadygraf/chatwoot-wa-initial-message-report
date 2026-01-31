from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> int:
    from interface_adapter.controllers.intent_coverage_cli import main as cli_main

    cli_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
