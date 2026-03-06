# chatwoot-wa-initial-message-report

Validador de conectividad a la API de Chatwoot con base de arquitectura limpia.

## Entrypoint
- `python3 run.py`

## Requisitos
- Python 3.10+
- Dependencias de `requirements.txt` (si tu entorno tiene `pip` disponible)

## Configuracion (.env)
Variables requeridas:
- `CHATWOOT_BASE_URL` (ej: `https://chatwoot.tu-dominio.com`)
- `CHATWOOT_ACCOUNT_ID` (entero)
- `CHATWOOT_API_ACCESS_TOKEN`

Variables opcionales:
- `CHATWOOT_TIMEOUT_SECONDS` (default `8`)

## Resultado esperado
- Exit code `0`: conectividad y autenticacion validas
- Exit code `1`: error de conexion, timeout, token/permisos invalidos o estado HTTP inesperado

El chequeo consulta:
- `GET /api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/inboxes`
