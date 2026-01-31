# chatwoot-wa-initial-message-report

CLI/TUI estilo AS/400 para verificar Chatwoot y MySQL y sincronizar cuentas, inboxes,
conversaciones y mensajes hacia MySQL.

## Que hace
- Health check de Chatwoot API y MySQL (`--json` disponible).
- Sincronizacion completa o solo mensajes usando conversaciones ya guardadas en MySQL.
- Listados rapidos desde MySQL (accounts, inboxes, conversations, messages).
- Menu AS/400 sin argumentos y TUI opcional (`--tui`).
- Wrapper `run.bat` para Windows y entrypoint `run_cli.py`.

## Requisitos
- Python 3.10.11
- MySQL/MariaDB accesible desde la maquina donde corre la CLI.
- Opcional: `textual` para `--tui` (`python -m pip install textual`).

## Configuracion (.env)
- `CHATWOOT_BASE_URL`
- `CHATWOOT_ACCOUNT_ID`
- `CHATWOOT_API_ACCESS_TOKEN`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `MYSQL_PORT` (opcional, default 3306)

Copia `.env.example` a `.env` y ajusta los valores.

## Instalacion
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Uso rapido
- `python run_cli.py` abre el menu AS/400 en terminal.
- `python run_cli.py --json` ejecuta el health check.
- `python run_cli.py --sync [--per-page N]` baja cuentas, inboxes, conversaciones y mensajes.
- `python run_cli.py --sync-messages [--per-page N] [--test ID]` solo mensajes usando las conversaciones guardadas.
- Listados: `--list-accounts`, `--list-inboxes`, `--list-conversations`, `--list-messages`.
- `python run_cli.py --tui` abre la interfaz TUI (requiere `textual`).
- En Windows: `run.bat --list-accounts` (usa la venv si existe).

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

## Tablas creadas en MySQL
- `1_accounts`
- `2_inboxes`
- `3_conversations`
- `4_messages`

### Requisitos MySQL
- La base de datos debe existir antes de sincronizar.
- Permisos: CREATE TABLE, INSERT, UPDATE, SELECT.
- Las tablas se crean con DEFAULT CHARSET=utf8mb4.

### Credenciales Chatwoot
- La API usa el header `api_access_token` con `CHATWOOT_API_ACCESS_TOKEN`.
- El `CHATWOOT_ACCOUNT_ID` se usa en la URL `/api/v1/accounts/{id}`.

## Notas de arquitectura
- Entrada por `run_cli.py` (o `run.bat`), que delega en `interface_adapter.controllers.cli`.
- Capas separadas (domain / application / interface_adapter / infrastructure) para mantener Clean Architecture y habilitar la futura extraccion de contextos.

## Flujo sugerido
1) Copia `.env.example` a `.env` y completa credenciales.
2) `python run_cli.py --json` para validar Chatwoot y MySQL.
3) `python run_cli.py --sync` para poblar las tablas.
4) Usa listados o la TUI (`--tui`) para navegar datos.

## Tests
- `pytest`
