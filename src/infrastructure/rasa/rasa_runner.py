import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from src.application.ports.rasa_runner import RasaRunner
from src.shared import config
from src.shared.logger import get_logger

logger = get_logger(__name__)


def _extract_port(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"http://{url}")
    if parsed.port:
        return str(parsed.port)
    return "5005"


class RasaCliRunner(RasaRunner):
    def __init__(self, project_path: str | None = None):
        self.project_path = project_path or str(Path(__file__).resolve().parent)

    def run_server(self) -> int:
        url = (config.RASA_BASE_URL or "").strip()
        if not url:
            raise RuntimeError("RASA_BASE_URL not set")
        port = _extract_port(url)
        cmd = [sys.executable, "-m", "rasa", "run", "--enable-api", "--cors", "*", "--port", port]
        logger.info("Starting Rasa server", port=port, cwd=self.project_path)
        return subprocess.call(cmd, cwd=self.project_path)

    def train(self) -> int:
        cmd = [sys.executable, "-m", "rasa", "train"]
        logger.info("Training Rasa model", cwd=self.project_path)
        return subprocess.call(cmd, cwd=self.project_path)
