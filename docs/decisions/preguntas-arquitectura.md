# Preguntas de Arquitectura Pendientes

### [2026-03-13] Definir politica de informacion expuesta en health endpoints
- **Contexto**: `/health` publica `chatwoot_base_url`; removerlo mejora hardening pero cambia contrato de respuesta.
- **Pregunta**: se mantiene metadata detallada en endpoint publico o se separa en endpoint interno protegido?
- **Opciones consideradas**:
  1. `/health` minimalista (solo estado) + `/health/details` autenticado.
  2. Mantener payload actual y restringir acceso por red/reverse proxy.
  3. Mantener payload actual con feature flag por entorno.
- **Decision**: (pendiente - escalado desde todo.md)
- **ADR resultante**: (pendiente)
