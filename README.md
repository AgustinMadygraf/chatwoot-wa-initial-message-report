# chatwoot-wa-initial-message-report

Validador de conectividad a la API de Chatwoot con base de arquitectura limpia.

## Entrypoint
- `python3 run.py`
- `python3 run.py contacts`

## Requisitos
- Python 3.10+
- Dependencias de `requirements.txt` (si tu entorno tiene `pip` disponible)

## Configuracion (.env)
Variables requeridas:
- `CHATWOOT_BASE_URL` (ej: `https://chatwoot.tu-dominio.com`)
- `CHATWOOT_ACCOUNT_ID` (entero)
- `CHATWOOT_API_ACCESS_TOKEN`

Valores hardcodeados en codigo:
- `CHATWOOT_TIMEOUT_SECONDS=8`
- `CHATWOOT_TLS_VERIFY=true`
- `CHATWOOT_CA_BUNDLE=certs/chatwoot-ca-bundle.pem`

## Resultado esperado
- Exit code `0`: conectividad y autenticacion validas
- Exit code `1`: error de conexion, timeout, token/permisos invalidos o estado HTTP inesperado

El chequeo consulta:
- `GET /api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/inboxes`

El reporte de contactos consulta:
- `GET /api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts`

## Troubleshooting SSL
Si aparece `CERTIFICATE_VERIFY_FAILED`, el servidor Chatwoot probablemente no este enviando bien la cadena completa o usa una CA no disponible localmente.

Opciones:
1. Recomendado: completar `certs/chatwoot-ca-bundle.pem` con la CA/intermedios correctos.
