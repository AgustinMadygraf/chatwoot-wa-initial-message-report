# chatwoot-wa-initial-message-report

Repositorio con:
- CLI/TUI estilo AS/400 para health check y sync de Chatwoot hacia MySQL.
- Bridge FastAPI para webhook de Chatwoot.

## Entrypoints
- `python run_chatwoot_sync.py` (CLI/TUI de sync y health check).
- `python run_chatwoot_bridge.py` (servidor FastAPI del webhook).
- `python run_intent_coverage_report.py` (actualmente deshabilitado).

## Requisitos
- Python 3.10.11
- MySQL/MariaDB accesible desde la maquina donde corre la CLI.
- Opcional: `textual` para `--tui` (`python -m pip install textual`).

## Instalacion
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configuracion (.env)
### Sync Chatwoot -> MySQL
- `CHATWOOT_BASE_URL`
- `CHATWOOT_ACCOUNT_ID`
- `CHATWOOT_API_ACCESS_TOKEN`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `MYSQL_PORT` (opcional, default 3306)
- `DEBUG_INBOXES=1` (opcional, log del payload de inboxes)

### Bridge
- `WEBHOOK_SECRET`
- `PORT` (bridge)

Opcional:
- `LOG_FORMAT=json` para logging estructurado.

## Uso rapido (Chatwoot sync)
- `python run_chatwoot_sync.py` abre el menu AS/400 en terminal.
- `python run_chatwoot_sync.py --json` ejecuta el health check.
- `python run_chatwoot_sync.py --sync [--per-page N]` baja cuentas, inboxes, conversaciones y mensajes.
- `python run_chatwoot_sync.py --sync-messages [--per-page N] [--test ID]` solo mensajes usando las conversaciones guardadas.
- Listados: `--list-accounts`, `--list-inboxes`, `--list-conversations`, `--list-messages`.
- `python run_chatwoot_sync.py --tui` abre la interfaz TUI (requiere `textual`).

## Bridge Chatwoot webhook
- Endpoint: `POST /webhook/{secret}`.
- Valida `secret` contra `WEBHOOK_SECRET`.
- Procesa solo eventos `message_created` con `message_type = incoming`.
- Si el payload no trae contenido, responde `"Ok"`.

## Reporte de intenciones
- `run_intent_coverage_report.py` está deshabilitado en esta rama.

## Tablas creadas en MySQL
- `1_accounts`
- `2_inboxes`
- `3_conversations`
- `4_messages`

## Tests
- `pytest`
