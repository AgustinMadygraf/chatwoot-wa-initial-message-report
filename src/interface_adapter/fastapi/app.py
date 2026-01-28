from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from src.shared.config import load_env_file
from src.shared.logger import get_logger
from src.use_cases.health_check import run_health_checks

APP_TITLE = "Chatwoot Connection Checker"
PUBLIC_LINK = "http://localhost:5006"


def create_app() -> FastAPI:
    load_env_file()
    app = FastAPI(title=APP_TITLE)
    logger = get_logger("fastapi")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return f"""
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{APP_TITLE}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="bg-light">
    <main class="container py-5">
      <div class="row justify-content-center">
        <div class="col-lg-8">
          <div class="card shadow-sm">
            <div class="card-body">
              <h1 class="h4 mb-3">{APP_TITLE}</h1>
              <p class="mb-1">Enlace publicado:</p>
              <p class="mb-3">
                <a href="{PUBLIC_LINK}" target="_blank" rel="noreferrer">{PUBLIC_LINK}</a>
              </p>
              <button id="checkBtn" class="btn btn-primary">Verificar conexión</button>
              <div id="status" class="mt-4"></div>
            </div>
          </div>
        </div>
      </div>
    </main>
    <script>
      const statusEl = document.getElementById('status');
      const checkBtn = document.getElementById('checkBtn');
      const render = (data) => {{
        const okBadge = (ok) => ok
          ? '<span class="badge bg-success">OK</span>'
          : '<span class="badge bg-danger">ERROR</span>';
        const item = (name, result) => `
          <div class="d-flex justify-content-between align-items-center border rounded p-2 mb-2">
            <div><strong>${{name}}</strong><div class="text-muted small">${{result.error || ''}}</div></div>
            ${{okBadge(result.ok)}}
          </div>`;
        statusEl.innerHTML = `
          <div class="mb-2">${{okBadge(data.ok)}} Resultado general</div>
          ${{item('Chatwoot API', data.chatwoot)}}
          ${{item('MySQL', data.mysql)}}
        `;
      }};
      checkBtn.addEventListener('click', async () => {{
        statusEl.innerHTML = '<div class="text-muted">Verificando...</div>';
        try {{
          const resp = await fetch('/api/status');
          const data = await resp.json();
          render(data);
        }} catch (err) {{
          statusEl.innerHTML = '<div class="text-danger">No se pudo verificar.</div>';
        }}
      }});
    </script>
  </body>
</html>
"""

    @app.get("/api/status", response_class=JSONResponse)
    def status() -> JSONResponse:
        payload = run_health_checks(logger=logger)
        return JSONResponse(payload)

    return app
