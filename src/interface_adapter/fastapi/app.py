from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.shared.config import load_env_file
from src.shared.logger import get_logger
from src.use_cases.health_check import run_health_checks

APP_TITLE = "Chatwoot Connection Checker"
PUBLIC_LINK = "http://localhost:5006"


def create_app() -> FastAPI:
    load_env_file()
    app = FastAPI(title=APP_TITLE)
    logger = get_logger("fastapi")
    templates = Jinja2Templates(directory="src/interface_adapter/fastapi/templates")
    app.mount("/static", StaticFiles(directory="src/interface_adapter/fastapi/static"), name="static")

    @app.get("/")
    def index(request: Request):
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "title": APP_TITLE, "public_link": PUBLIC_LINK},
        )

    @app.get("/api/status", response_class=JSONResponse)
    def status() -> JSONResponse:
        payload = run_health_checks(logger=logger)
        return JSONResponse(payload)

    return app
