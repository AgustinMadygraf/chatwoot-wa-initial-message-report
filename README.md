# chatwoot-sync-report

Sincroniza datos de Chatwoot a MySQL usando la API: accounts, inboxes, conversaciones y mensajes.

## Requisitos
- Python 3.10.11
- MySQL/MariaDB

## Configuracion (.env)
Variables:
- `CHATWOOT_BASE_URL`
- `CHATWOOT_ACCOUNT_ID`
- `CHATWOOT_API_ACCESS_TOKEN`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `MYSQL_PORT`

## Uso
Activar venv:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Sincronizar:
```bash
python run_cli.py --sync
```

Listados:
```bash
python run_cli.py --list-accounts
python run_cli.py --list-inboxes
python run_cli.py --list-conversations
python run_cli.py --list-messages
```

Opcional:
```bash
python run_cli.py --sync --per-page 50
```

Menu AS/400 (sin argumentos):
```bash
python run_cli.py
```

Windows shortcut:
```bat
run.bat --list-accounts

## Tablas en MySQL
- `1_accounts`
- `2_inboxes`
- `3_conversations`
- `4_messages`
```
