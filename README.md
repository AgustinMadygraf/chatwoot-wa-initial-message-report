# chatwoot-wa-initial-message-report

Repositorio unificado con:
- CLI/TUI estilo AS/400 para health check y sync de Chatwoot hacia MySQL.
- Bridge FastAPI entre Chatwoot y Rasa (webhook).
- Scripts para correr/entrenar Rasa y abrir tunel ngrok.

## Entrypoints
- `python run_chatwoot_sync.py` (CLI/TUI de sync y health check).
- `python run_chatwoot_rasa_bridge.py` (servidor FastAPI del webhook).
- `python run_rasa_server.py` (levanta Rasa).
- `python run_rasa_train.py` (entrena modelo Rasa).
- `python run_ngrok_tunnel.py` (abre tunel ngrok).

## Requisitos
- Python 3.10.11
- MySQL/MariaDB accesible desde la maquina donde corre la CLI.
- `ngrok` CLI disponible en PATH para `run_ngrok_tunnel.py`.
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

### Bridge / Rasa / Ngrok
- Los valores se encuentran hardcodeados en `src/shared/config.py`.
- Si necesitas cambiarlos, modifica ese archivo.

Opcional:
- `LOG_FORMAT=json` para logging estructurado.

## Uso rapido (Chatwoot sync)
- `python run_chatwoot_sync.py` abre el menu AS/400 en terminal.
- `python run_chatwoot_sync.py --json` ejecuta el health check.
- `python run_chatwoot_sync.py --sync [--per-page N]` baja cuentas, inboxes, conversaciones y mensajes.
- `python run_chatwoot_sync.py --sync-messages [--per-page N] [--test ID]` solo mensajes usando las conversaciones guardadas.
- Listados: `--list-accounts`, `--list-inboxes`, `--list-conversations`, `--list-messages`.
- `python run_chatwoot_sync.py --tui` abre la interfaz TUI (requiere `textual`).

### Opciones del CLI
- `--json`: health check en JSON (solo aplica cuando no hay otra accion).
- `--debug`: logs verbosos.
- `--per-page N`: pagina llamadas a la API (conversaciones/mensajes).
- `--test ID`: solo para `--sync-messages`; limita a una conversacion (si omites ID usa la primera).

### Navegacion AS/400 (CLI sin --tui)
- Menu numerico (1-6) en el modo CLI sin argumentos.
- Paginado en tablas: F8/F9 o N/P (tambien flechas izq/der).
- Salir: F3, ESC o Q. Refrescar: F5.

### Navegacion TUI (Textual)
- F1 ayuda, F3 salir, F5 refresh.
- F8/F9 pagina tablas.
- 1-4 cambia dataset (cuentas, inboxes, conversaciones, mensajes).

## Bridge Chatwoot <-> Rasa
- Endpoint: `POST /webhook/{secret}`.
- Valida `secret` contra `WEBHOOK_SECRET`.
- Procesa solo eventos `message_created` con `message_type = incoming`.
- Si Rasa responde texto, usa el primer mensaje; si no, responde `"Bot no activado"`.
- Si el payload no trae contenido, responde `"Ok"`.

Ejemplo de payload:
```json
{
  "event": "message_created",
  "message_type": "incoming",
  "account": { "id": 1 },
  "conversation": { "id": 123 },
  "content": "Hola"
}
```

Ejemplo de respuesta:
```json
{
  "ok": true,
  "status": 200,
  "detail": "..."
}
```

## Rasa
- El proyecto Rasa vive en `src/infrastructure/rasa` (config.yml, domain.yml, data/, models/).
- `run_rasa_server.py` ejecuta `rasa run --enable-api --cors *` con el puerto derivado de `RASA_BASE_URL`.
- `run_rasa_train.py` ejecuta `rasa train` dentro de `src/infrastructure/rasa`.

## Ngrok
- `run_ngrok_tunnel.py` ejecuta `ngrok http <PORT> --domain <domain>`.
- El dominio se extrae desde `URL_WEBHOOK`.

## Tablas creadas en MySQL
- `1_accounts`
- `2_inboxes`
- `3_conversations`
- `4_messages`

### Requisitos MySQL
- La base de datos debe existir antes de sincronizar.
- Permisos: CREATE TABLE, INSERT, UPDATE, SELECT.
- Las tablas se crean con DEFAULT CHARSET=utf8mb4.

## Tests
- `pytest`
