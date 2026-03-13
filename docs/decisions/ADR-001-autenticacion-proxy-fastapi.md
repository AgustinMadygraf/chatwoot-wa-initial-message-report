# ADR-001: Autenticacion de consumidores del proxy FastAPI

## Estado
- **Fecha**: 2026-03-13
- **Estado**: Aceptada
- **Decisores**: Agente (decision-helper), pendiente validacion final del usuario

## Contexto
El servicio FastAPI expone endpoints proxy hacia Chatwoot usando credenciales internas del backend (`CHATWOOT_API_ACCESS_TOKEN`).
Actualmente los endpoints `/api/v1/accounts/*` no exigen autenticacion del consumidor del proxy.
Esto permite acceso no controlado a datos sensibles de inboxes/contactos para cualquier actor con conectividad de red al servicio.

## Decision
**Opcion seleccionada**: API Key estatica por entorno (header dedicado en FastAPI).

**Justificacion**:
- Mitiga de forma inmediata el riesgo critico de acceso no autorizado.
- Es simple de implementar, auditar y operar sin infraestructura extra.
- Es reversible y permite migracion incremental posterior a JWT o mTLS si el sistema crece.
- Evita bloquear el roadmap funcional inmediato (conversations/messages).

## Consecuencias

### Positivas
- Cierra el hueco principal de seguridad en la interfaz proxy.
- Bajo esfuerzo de implementacion y validacion automatizada.
- Menor complejidad operativa respecto a JWT/mTLS en esta etapa.

### Negativas / Trade-offs
- Rotacion y distribucion manual de claves.
- No incorpora identidad fina por usuario/servicio (solo secreto compartido).
- Menor trazabilidad que un esquema JWT con claims.

## Alternativas rechazadas

### Opcion: JWT firmado (scopes/roles)
**Por que se rechazo**:
- Mayor costo inicial (issuer, validacion de claims, clock skew, rotacion de keys).
- Exceso de complejidad para el alcance actual y sin requerimiento multi-tenant fuerte.

### Opcion: mTLS interno
**Por que se rechazo**:
- Alta complejidad de infraestructura (PKI, provision, renovacion certs).
- Menor agilidad para equipos que hoy operan sin malla/ingress con mTLS gestionado.

## Implementacion
- **Plan de accion**: ver `docs/todo.md` (seccion ADR-001)
- **Responsable**: agente + validacion usuario

## Notas
- Objetivo minimo: header obligatorio `X-Proxy-Api-Key` validado contra variable de entorno dedicada.
- Evolucion prevista: migrar a JWT cuando haya necesidad de permisos granulares por consumidor.
