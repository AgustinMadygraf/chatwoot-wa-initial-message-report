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

### [2026-03-13] Definir estrategia de arranque ante fallos de bootstrap
- **Contexto**: durante `lifespan` se captura excepcion generica y el servicio continua en modo degradado sin cliente proxy operativo.
- **Pregunta**: el servicio debe fallar al iniciar (fail-fast) o continuar degradado con salud no-operativa?
- **Opciones consideradas**:
  1. Fail-fast: abortar startup ante error de inicializacion critica.
  2. Degradado controlado: iniciar, exponer estado no-operativo y bloquear endpoints de negocio.
  3. Estrategia mixta por entorno (estricto en prod, degradado en dev).
- **Decision**: (pendiente - escalado desde todo.md)
- **ADR resultante**: (pendiente)
