# Chatwoot API vs FastAPI Local: Endpoint Gap Analysis

Fecha de analisis: 2026-03-15

## Objetivo

Documentar que endpoints de la API oficial de Chatwoot ya estan replicados por esta interfaz FastAPI local, cuales faltan, y cual es el pendiente mas importante para el objetivo del proyecto (reporte de mensaje inicial de WhatsApp).

## Alcance evaluado

- Implementacion local FastAPI: `src/infrastructure/fastapi_app/app.py`
- Controllers/proxy local: `src/interface_adapter/controllers/fastapi_proxy_controllers.py`, `src/infrastructure/requests/chatwoot_fastapi_proxy_client.py`
- API oficial de Chatwoot (Application API, foco en `contacts`, `inboxes`, `conversations`, `messages`)

## Endpoints replicados en FastAPI

Implementados actualmente en la interfaz local:

1. `GET /api/v1/accounts/{account_id}/inboxes`
2. `GET /api/v1/accounts/{account_id}/inboxes/{inbox_id}`
3. `GET /api/v1/accounts/{account_id}/contacts`
4. `GET /api/v1/accounts/{account_id}/contacts/{id}`
5. `GET /api/v1/accounts/{account_id}/conversations`
6. `GET /api/v1/accounts/{account_id}/conversations/{conversation_id}`
7. `GET /api/v1/accounts/{account_id}/conversations/{conversation_id}/messages`

Notas de comportamiento local:

- `GET /contacts` acepta `page=N` y extension local `page=all`.
- `GET /conversations` acepta `page=N`, `status` e `inbox_id`.
- `GET /conversations/{conversation_id}` aplica sanitizacion explicita de campos sensibles.
- `GET /conversations/{conversation_id}/messages` aplica la misma politica explicita en `payload` y `meta`.
- Se fuerza `account_id` contra `CHATWOOT_ACCOUNT_ID` configurado en `.env`.

## Endpoints pendientes (priorizados por impacto funcional)

### 1) Alta prioridad operativa

Familia `contacts` aun no replicada completamente:

- `POST /api/v1/accounts/{account_id}/contacts`
- `PUT /api/v1/accounts/{account_id}/contacts/{id}`
- `DELETE /api/v1/accounts/{account_id}/contacts/{id}`
- Endpoints de busqueda/filtro y vinculaciones (ejemplo: conversaciones del contacto, inboxes contactables, labels)

Familia `inboxes` de administracion:

- `POST /api/v1/accounts/{account_id}/inboxes`
- Otros endpoints de configuracion de inbox

### 2) Pendiente amplio (fuera del foco inmediato)

- Resto de `Application API` no cubierto por este proyecto
- `Client API`
- `Platform API`

## Pendiente mas importante (single choice)

Endpoint mas importante a implementar primero:

1. `GET /api/v1/accounts/{account_id}/contacts/{id}/conversations`

Justificacion:

- Permite recortar el analisis por contacto sin barrer todas las conversaciones.
- Reduce costo de consultas para orquestadores remotos (OpenClaw) en red no confiable.
- Mejora calidad de contexto para KPIs por cliente/lead.

## Fuentes oficiales consultadas

- https://developers.chatwoot.com/api-reference/introduction
- https://developers.chatwoot.com/api-reference/inboxes/list-all-inboxes
- https://developers.chatwoot.com/api-reference/inboxes/get-an-inbox
- https://developers.chatwoot.com/api-reference/contacts/list-contacts
- https://developers.chatwoot.com/api-reference/contacts/show-contact
- https://developers.chatwoot.com/api-reference/contacts/create-contact
- https://developers.chatwoot.com/api-reference/contacts/update-contact
- https://developers.chatwoot.com/api-reference/contacts/delete-contact
- https://developers.chatwoot.com/api-reference/contacts/contact-conversations
- https://developers.chatwoot.com/api-reference/conversations/conversations-list
- https://developers.chatwoot.com/api-reference/conversations/conversation-details
- https://developers.chatwoot.com/api-reference/messages/get-messages

## Evidencia de implementacion local

- `src/infrastructure/fastapi_app/app.py`
- `src/interface_adapter/controllers/fastapi_proxy_controllers.py`
- `src/infrastructure/requests/chatwoot_fastapi_proxy_client.py`

