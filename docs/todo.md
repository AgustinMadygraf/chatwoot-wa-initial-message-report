# Agenda de Tareas de Codigo (`docs/todo.md`)

## Hallazgos Auditados (resueltos en esta iteracion)

- [x] [ADVERTENCIA][DIP] `ChatwootFastApiProxyClient` dependia directamente de `requests.get`.
  - Archivo: `src/infrastructure/requests/chatwoot_fastapi_proxy_client.py`
  - Mejora aplicada: inyeccion de `AsyncHttpTransport` con `HttpxAsyncTransport` por defecto.
  - Impacto: reduce acoplamiento y habilita evolucion del cliente HTTP sin tocar casos de uso.

- [x] [ADVERTENCIA][DIP] `ChatwootRequestsGateway` dependia directamente de `requests.get`.
  - Archivo: `src/infrastructure/requests/chatwoot_requests_gateway.py`
  - Mejora aplicada: inyeccion de `SyncHttpTransport` y jerarquia de errores de transporte.
  - Impacto: mejora testabilidad y elimina dependencia directa de libreria concreta en gateways.

- [x] [ADVERTENCIA][ISP] Contrato de respuesta HTTP estaba acoplado a `requests.Response`.
  - Archivo: `src/infrastructure/requests/http_transport.py`
  - Mejora aplicada: protocolo `HttpResponse` + contratos `SyncHttpTransport` y `AsyncHttpTransport`.

- [x] [ADVERTENCIA][Escalabilidad] Endpoints FastAPI ejecutaban flujo bloqueante.
  - Archivo: `src/infrastructure/fastapi/app.py`, `src/interface_adapter/controllers/fastapi_proxy_controllers.py`
  - Mejora aplicada: handlers y controllers `async`, con cliente proxy asincronico.

- [x] [ADVERTENCIA][Performance] Se creaba `httpx.AsyncClient` potencialmente por request en fallback.
  - Archivo: `src/infrastructure/fastapi/app.py`
  - Mejora aplicada: ciclo de vida unico via `lifespan` (startup/shutdown) y cliente compartido.

- [x] [CRITICO][Seguridad] sanitizacion de secretos era sensible a mayusculas/minusculas en claves.
  - Archivo: `src/infrastructure/requests/sensitive_data_sanitizer.py`
  - Problema: `API_KEY` y `Authorization` no eran detectados siempre como sensibles.
  - Mejora aplicada: normalizacion de clave (`normalized_key`) antes de chequear `SENSITIVE_KEYS`.

## Tareas Pendientes

- [ ] Ninguna tarea tecnica pendiente detectada para la migracion `requests` -> `httpx` en alcance actual.
