# Preguntas de Arquitectura Pendientes

### [2026-03-13] Proteger API proxy con autenticacion y autorizacion de cliente
- **Contexto**: el servicio FastAPI expone endpoints proxy hacia Chatwoot usando credenciales internas, pero hoy no exige autenticacion del consumidor.
- **Pregunta**: cual es el mecanismo de autenticacion/autorizacion a estandarizar para `/api/v1/accounts/*`?
- **Opciones consideradas**:
  1. API Key estatica por entorno.
  2. JWT firmado (con scopes/roles).
  3. mTLS entre servicios internos.
- **Decision**: (pendiente - escalado desde todo.md)
- **ADR resultante**: (pendiente)

### [2026-03-13] Definir politica de informacion expuesta en health endpoints
- **Contexto**: `/health` publica `chatwoot_base_url`; removerlo mejora hardening pero cambia contrato de respuesta.
- **Pregunta**: se mantiene metadata detallada en endpoint publico o se separa en endpoint interno protegido?
- **Opciones consideradas**:
  1. `/health` minimalista (solo estado) + `/health/details` autenticado.
  2. Mantener payload actual y restringir acceso por red/reverse proxy.
  3. Mantener payload actual con feature flag por entorno.
- **Decision**: (pendiente - escalado desde todo.md)
- **ADR resultante**: (pendiente)
