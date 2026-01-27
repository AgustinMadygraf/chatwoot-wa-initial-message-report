# Como obtener credenciales de Chatwoot

Este documento describe como obtener los valores necesarios para ejecutar el reporte:

- `CHATWOOT_BASE_URL`
- `CHATWOOT_ACCOUNT_ID`
- `CHATWOOT_API_ACCESS_TOKEN`
- `CHATWOOT_INBOX_ID`

## 1) Base URL
Usa la URL base donde esta instalado Chatwoot. Ejemplos:
- Cloud: `https://app.chatwoot.com`
- Self-hosted: `https://chatwoot.tu-dominio.com`

El valor debe apuntar a la raiz del servidor (sin `/api`).

## 2) Account ID
En Chatwoot, cada workspace tiene un `account_id`.

Opciones comunes para obtenerlo:
- Desde el URL del navegador cuando estas dentro del workspace (suele aparecer como `/app/accounts/<account_id>/...`).
- Desde la UI, en algunos despliegues figura en **Settings** o **Account settings**.

## 3) API Access Token
Necesitas un token personal de acceso.

Pasos generales:
1. Inicia sesion en Chatwoot.
2. Ve a **Profile settings** (tu avatar o perfil).
3. Busca la seccion **Access Tokens** o **API Access Tokens**.
4. Crea un token nuevo y copialo.

Guarda este token de forma segura; no lo compartas ni lo subas al repo.

## 4) Inbox ID (WhatsApp Cloud)
El `inbox_id` identifica el canal especifico.

Opciones para encontrarlo:
- En la UI, ve a **Inboxes** y abre el inbox de WhatsApp Cloud.
- En la URL del navegador suele aparecer como `/app/accounts/<account_id>/settings/inboxes/<inbox_id>`.

## 5) Crear el .env local
Con los valores anteriores, crea un archivo `.env` en la raiz del repo:

```
CHATWOOT_BASE_URL=https://tu-chatwoot.example.com
CHATWOOT_ACCOUNT_ID=123
CHATWOOT_API_ACCESS_TOKEN=token_aqui
CHATWOOT_INBOX_ID=456
CHATWOOT_DAYS=15
```

Luego puedes ejecutar el CLI con solo:

```
python -m chatwoot_wa_initial_message_report
```
