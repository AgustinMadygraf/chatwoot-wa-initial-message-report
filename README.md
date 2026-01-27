# chatwoot-wa-initial-message-report

Extrae, usando SOLO la API de Chatwoot, el primer mensaje entrante (texto) de cada conversacion de un inbox especifico (WhatsApp Cloud) y genera 3 CSV de reporte.

## Que hace
- Lista conversaciones del inbox indicado.
- Para cada conversacion obtiene el detalle y busca el primer mensaje entrante del contacto.
- Excluye mensajes privados, no-texto y no provenientes del contacto.
- Normaliza el texto (lower + trim + colapsar espacios) y clasifica por categoria usando regex.
- Genera CSV crudos y agregados.

## Configuracion
Variables de entorno soportadas:
- `CHATWOOT_BASE_URL`
- `CHATWOOT_ACCOUNT_ID`
- `CHATWOOT_API_ACCESS_TOKEN`
- `CHATWOOT_INBOX_ID`
- `CHATWOOT_DAYS`

Ejemplo `.env.example` incluido sin secretos.

## Ejecucion
```bash
python -m chatwoot_wa_initial_message_report \
  --base-url https://your-chatwoot.example.com \
  --account-id 123 \
  --api-token your_token \
  --inbox-id 456 \
  --days 15
```

Con fecha fija:
```bash
python -m chatwoot_wa_initial_message_report \
  --base-url https://your-chatwoot.example.com \
  --account-id 123 \
  --api-token your_token \
  --inbox-id 456 \
  --since 2026-01-01
```

Si no se especifica `--days` ni `--since`, se procesa todo lo disponible.

## Salidas (CSV)
Se escriben en `./data` (se crea si no existe):

1) `data/initial_messages_raw.csv` (1 fila por conversacion procesada)
- conversation_id
- inbox_id
- conversation_created_at
- message_id
- message_created_at
- initial_message_raw
- initial_message_literal
- category

2) `data/initial_messages_table_literal.csv` (agregacion por literal)
- initial_message_literal
- cantidad
- porcentaje_total

3) `data/initial_messages_table_category.csv` (agregacion por categoria)
- category
- cantidad
- porcentaje_total

## Definicion de "mensaje inicial"
- Primer mensaje ENTRANTE del contacto dentro de cada conversacion.
- Solo `content_type == "text"` y `content` no vacio.
- Se excluyen mensajes privados (`private = true`) y mensajes con `sender_type != "contact"`.

## Limitaciones
- Solo usa la API de Chatwoot; no accede a DB ni RASA.
- Depende de la respuesta de la API para el orden y disponibilidad de mensajes.
- Usa backoff simple para 429 y 5xx.

## Desarrollo
Dependencias principales: `requests`, `pandas`.

Tests:
```bash
pytest
```
