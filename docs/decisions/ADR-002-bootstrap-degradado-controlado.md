# ADR-002: Estrategia de arranque en modo degradado controlado para proxy FastAPI

## Estado
- **Fecha**: 2026-03-13
- **Estado**: Aceptada
- **Decisores**: Agente (decision-helper), pendiente validacion final del usuario

## Contexto
Durante el `lifespan` del servicio FastAPI, pueden fallar dependencias de inicializacion (configuracion o conectividad hacia Chatwoot).
La pregunta abierta era si el servicio debe abortar startup (fail-fast) o iniciar en modo degradado.
Hoy el comportamiento real ya es cercano a degradado: se registra el error y el proxy queda inhabilitado.

## Decision
**Opcion seleccionada**: Degradado controlado.

**Justificacion**:
- Mantiene disponibilidad de endpoints operativos/diagnostico (`/`, `/health`) aun cuando Chatwoot no este listo.
- Evita reinicios continuos por fallos transitorios de dependencia externa.
- Es coherente con el estado actual del codigo y de menor riesgo de cambio inmediato.

## Consecuencias

### Positivas
- Mejor resiliencia ante fallos transitorios de bootstrap.
- Operacion y troubleshooting mas simples (servicio responde, reporta estado).
- Menor probabilidad de downtime total por dependencia externa.

### Negativas / Trade-offs
- Requiere contracto claro de readiness (degradado vs operativo).
- Riesgo de confusion si consumidores no distinguen estado degradado.
- Necesita tests de comportamiento en modo degradado.

## Alternativas rechazadas

### Opcion: Fail-fast estricto
**Por que se rechazo**:
- Puede provocar indisponibilidad total del servicio ante fallos externos temporales.
- Aumenta sensibilidad operativa y complejidad de recuperación.

### Opcion: Estrategia mixta por entorno
**Por que se rechazo**:
- Agrega complejidad de configuracion y caminos de ejecucion multiples.
- No aporta valor inmediato para el alcance actual.

## Implementacion
- **Plan de accion**: ver `docs/todo.md` (seccion ADR-002)
- **Responsable**: agente + validacion usuario

## Notas
- Recomendacion operativa: exponer estado degradado de forma explicita y usar `503` para endpoints de negocio no disponibles.
- Mantener logs estructurados de causa raiz en bootstrap.
