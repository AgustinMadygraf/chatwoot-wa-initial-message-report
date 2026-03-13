# Agenda de Tareas de Codigo (`docs/todo.md`)

Backlog activo. Las tareas cerradas se registran en `docs/todo.done.md`.

## Tareas Pendientes

### [ADR-002] Formalizar modo degradado controlado
- [ ] Hacer explicito el estado operativo/degradado en healthcheck.
  - **Archivo**: `src/infrastructure/fastapi/app.py`
  - **Cambio**: devolver estado legible para operaciones (operativo/degradado) sin romper seguridad.

- [ ] Estandarizar codigo HTTP cuando el proxy no esta listo.
  - **Archivo**: `src/infrastructure/fastapi/app.py`
  - **Cambio**: retornar `503 Service Unavailable` para endpoints de negocio cuando `_proxy_client` no este inicializado.

- [ ] Agregar tests de comportamiento en degradado.
  - **Archivo**: `tests/` (nuevo modulo de readiness/degraded mode)
  - **Cambio**: cubrir health y rutas de negocio con proxy no inicializado.

- [ ] Validar implementacion.
  - `python -m pytest -q`

**Referencia**: `docs/decisions/ADR-002-bootstrap-degradado-controlado.md`
**Prioridad**: Alta

## Dudas de Alto Nivel (Registradas en docs/decisions/)

Ver `docs/decisions/preguntas-arquitectura.md` para decisiones arquitectonicas pendientes.
