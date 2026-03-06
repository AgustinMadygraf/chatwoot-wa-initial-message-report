# chatwoot-wa-initial-message-report

Repositorio con un bridge webhook para Chatwoot y lógica de dominio/use cases asociados.

## Entrypoint
- `python run_chatwoot_bridge.py` (servidor FastAPI del webhook).

## Requisitos
- Python 3.10+

## Instalacion
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Configuracion (.env)
- `CHATWOOT_BASE_URL`
- `CHATWOOT_BOT_TOKEN` (o `CHATWOOT_API_ACCESS_TOKEN`)
- `WEBHOOK_SECRET`
- `PORT` (opcional, default 8000)

Opcional:
- `LOG_FORMAT=json`

## Webhook
- Endpoint: `POST /webhook/{secret}`
- Valida `secret` contra `WEBHOOK_SECRET`.
- Procesa eventos `message_created` con `message_type = incoming`.

## Tests
- `pytest`
