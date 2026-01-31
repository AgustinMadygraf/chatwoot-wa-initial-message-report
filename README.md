# chatwoot-wa-initial-message-report

Repositorio unificado con:
- CLI/TUI estilo AS/400 para health check y sync de Chatwoot hacia MySQL.
- Bridge FastAPI entre Chatwoot y Rasa (webhook).
- Scripts para correr/entrenar Rasa y abrir tunel ngrok.

## Entrypoints
- `python run_chatwoot_sync.py` (CLI/TUI de sync y health check).
- `python run_chatwoot_rasa_bridge.py` (servidor FastAPI del webhook).
- `python run_intent_coverage_report.py` (reporte de intenciones desde MySQL).
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
- `WEBHOOK_SECRET`
- `PORT` (bridge)
- `URL_WEBHOOK` (ngrok)
- `RASA_BASE_URL`
- `RASA_REST_URL` (opcional, override de `RASA_BASE_URL` para webhook REST)
- `RASA_PARSE_URL` (opcional, override para `/model/parse`)
- `INTENT_MIN_COUNT` (opcional, default 5)
- `INTENT_PROGRESS_EVERY` (opcional, default 200)
- `INTENT_SCAN_PROGRESS_EVERY` (opcional, default 5000)

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

## Reporte de intenciones
- Requiere Rasa corriendo con API (`rasa run --enable-api`).
- Usa `/model/parse` para inferir intenciones sobre los mensajes guardados en MySQL (tabla `4_messages`).
- El script lee `src/infrastructure/rasa/data/nlu.yml` por defecto, pero puedes pasar `--nlu-file` para otro YAML.
- Tipos de ejecución:
  - `python run_intent_coverage_report.py --min-count 5` muestra cuántos mensajes cayeron en cada intención entrenada y qué intenciones quedan por encima o debajo del umbral configurado.
  - `--parse-url` sobrescribe `RASA_PARSE_URL`.
  - `--timeout` ajusta el timeout de la solicitud a Rasa.
  - `--debug` activa logs más verbosos.
-  - `--limit N` procesa solo los primeros `N` mensajes para obtener un reporte rápido sin recorrer toda la tabla.
-  - `--samples N` muestra los primeros N textos junto con la intención inferida y la confianza para que puedas inspeccionar ejemplos reales.
- Variables de configuración adicionales:
  - `RASA_PARSE_URL` (si no está, se arma como `RASA_BASE_URL` + `/model/parse`).
  - `INTENT_MIN_COUNT` (default 5) se usa cuando no pusiste `--min-count`.
- `INTENT_PROGRESS_EVERY` (default 200) controla con qué frecuencia el parser imprime progreso.
- `INTENT_SCAN_PROGRESS_EVERY` (default 5000) controla el log de mensajes procesados.
- El report muestra: totaales de parseos, porcentaje de mensajes con intención explícita, las intenciones entrenadas con su `Count/Pct/Status`, cuáles están por debajo del umbral, las intenciones no definidas en `nlu.yml` y (si pedís `--samples`) unos ejemplos de texto + intención + confianza.

## Ngrok
- `run_ngrok_tunnel.py` ejecuta `ngrok http <PORT>`.
- Si `URL_WEBHOOK` tiene dominio, agrega `--domain <domain>` (requiere plan pago).

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
