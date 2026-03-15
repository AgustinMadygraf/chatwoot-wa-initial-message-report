# chatwoot-wa-initial-message-report

Validador de conectividad a la API de Chatwoot con base de arquitectura limpia.

## Entrypoint
- `python3 run.py`
- `python3 run.py contacts`
- `python3 run.py doctor`
- `python3 run.py setup-security`

## Uso del comando contacts
- `python3 run.py contacts` muestra tabla formateada (comportamiento por defecto).
- `python3 run.py contacts --json` muestra el body JSON crudo de la respuesta de Chatwoot.
- `python3 run.py contacts --json` incluye `endpoint`, `status_code`, `headers` y `body`.

## Requisitos
- Python 3.10+
- Dependencias de `requirements.txt` (si tu entorno tiene `pip` disponible)

## Configuracion (.env)
Variables requeridas:
- `CHATWOOT_BASE_URL` (ej: `https://chatwoot.tu-dominio.com`)
- `CHATWOOT_ACCOUNT_ID` (entero)
- `CHATWOOT_API_ACCESS_TOKEN`
- `PROXY_API_KEY`

Bootstrap rapido:
- `python3 run.py setup-security` genera `PROXY_API_KEY` en `.env` y crea `certs/chatwoot-ca-bundle.pem`.
- Alternativa script directo: `python3 scripts/bootstrap_security.py`.

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

## FastAPI como interfaz de Chatwoot (produccion)
La app FastAPI ya no usa fixtures locales: consulta Chatwoot real via API
usando las credenciales del `.env`.

Endpoints expuestos:
- `GET /health`
- `GET /api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/inboxes`
- `GET /api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts?page=N`
- `GET /api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts?page=all`
- `GET /api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts/{CONTACT_ID}`

Autenticacion del proxy:
- Header requerido: `X-Proxy-Api-Key: <PROXY_API_KEY>`
- Sin header valido: respuesta `401 Unauthorized`

Nota: los datos devueltos son los de Chatwoot (upstream). Si los campos
`es_contacto_calificado`, `es_cliente`, `xubio_customer_id`, etc. existen en
`custom_attributes`, se devuelven tal cual.

Arranque:
- `python3 run_fastapi.py`

Configuracion sugerida para ejecutar la interfaz FastAPI local:
- `CHATWOOT_BASE_URL=https://chatwoot.tu-dominio.com`
- `CHATWOOT_ACCOUNT_ID=<tu_account_id>`
- `CHATWOOT_API_ACCESS_TOKEN=<tu_token>`
- `PROXY_API_KEY=<tu_clave_proxy>`

## Documentacion adicional
- Ver analisis de cobertura de API: [docs/api/chatwoot-fastapi-endpoint-gap.md](docs/api/chatwoot-fastapi-endpoint-gap.md)
