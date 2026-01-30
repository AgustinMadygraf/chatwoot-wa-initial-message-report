# AGENTS.md

## Contexto del proyecto
- App con entrypoint CLI: `run_cli.py` (o `run.bat`).
- Arquitectura en capas dentro de `src/` (entities, use_cases, interface_adapter, infrastructure, shared).
- Monolito modular orientado a extraer contextos en el futuro (Inventory/Ordering/Reporting).

## Convenciones
- Configuracion por variables de entorno en `.env`.
- El endpoint de estado debe informar conectividad a Chatwoot API y MySQL.
- No acoplar dominio y casos de uso a frameworks (Clean Architecture).
- UI/UX tipo AS/400 debe vivir como adaptador externo (CLI/TUI) sin contaminar dominio.
- Sin argumentos, la CLI muestra menu AS/400 interactivo.
- La UI ajusta ancho/alto automaticamente segun terminal y pagina con F8/F9 (N/P).

## Variables de entorno esperadas
- `CHATWOOT_BASE_URL`
- `CHATWOOT_ACCOUNT_ID`
- `CHATWOOT_API_ACCESS_TOKEN`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `MYSQL_PORT` (opcional, default 3306)

## Objetivo por fases (resumen operativo)
- Fase 1: base tecnica enterprise (arquitectura, calidad, CI/CD).
- Fase 2: UI/UX AS/400 (TUI/CLI) sin romper capas.

## Lineamientos de arquitectura
- Capas: Domain -> Application -> Interface Adapters -> Frameworks/Drivers.
- DDD: entidades, value objects, agregados, repositorios (interfaces), domain events si aplica.
- Patrones: Repository, Unit of Work, Adapter, Factory, Strategy (cuando haya variaciones).
- Errores: usar tipos propios en dominio/aplicacion; mapear a mensajes en adapters.

## Calidad y tooling (target)
- Python 3.10.11, type hints completos, dataclasses donde aplique.
- Lint/format/typecheck: ruff + black + mypy.
- Tests: pytest (unit + integration minima).
- Logging estructurado (JSON) en infraestructura y adapters.

## CI/CD (target)
- Pipeline: lint -> format check -> typecheck -> tests -> coverage -> build.
- Versionado SemVer + changelog + releases por tag.
