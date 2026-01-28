# AGENTS.md

## Contexto del proyecto
- App con entrypoint CLI: `run_cli.py`.
- Arquitectura en capas dentro de `src/` (entities, use_cases, interface_adapter, infrastructure, shared).

## Convenciones
- Configuración por variables de entorno en `.env`.
- El endpoint de estado debe informar conectividad a Chatwoot API y MySQL.

## Variables de entorno esperadas
- `CHATWOOT_BASE_URL`
- `CHATWOOT_ACCOUNT_ID`
- `CHATWOOT_API_ACCESS_TOKEN`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `MYSQL_PORT` (opcional, default 3306)
