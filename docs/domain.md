# Dominio (Fase 1)

## Bounded Contexts (propuesto)
- **Comunicaciones**: conversaciones, mensajes, inboxes (Chatwoot).
- **Sincronizacion**: orquesta sync y health check.
- **Infraestructura**: DB, API externa, CLI/TUI.

## Lenguaje ubicuo (glosario)
- **Inbox**: canal de entrada (WhatsApp, Email, Web).
- **Conversation**: hilo de conversacion.
- **Message**: mensaje dentro de una conversacion.
- **Sync**: proceso de carga y persistencia local.
- **Health Check**: estado de conectividad API + DB.

## Reglas basicas
- Sync escribe en DB de forma idempotente (upsert).
- Mensajes se guardan con metadatos disponibles.
