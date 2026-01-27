# Informe para CODEX — Chatwoot API: endpoint de conversaciones devuelve 0 (UI muestra conversaciones)

## 1) Resumen ejecutivo

* La API de Chatwoot responde correctamente y autentica el token (200 en endpoints base).
* Los **contactos** se listan con datos (hay contenido a nivel account).
* El endpoint de **conversaciones** devuelve **0 resultados**, incluso sin filtro por inbox.
* En la **UI** del inbox “Whatsapp API” (id=2) se ven **~144 conversaciones**.

**Conclusión preliminar:** hay una **discrepancia de permisos/alcance (scope) del usuario dueño del token** vs lo que se ve en UI, o bien **la membresía al inbox no quedó persistida** (botón “Actualizar”), o existe un **filtro implícito** en la API (por estado/asignación/paginación) que deja el resultado vacío.

---

## 2) Contexto y evidencia observada

### 2.1 Endpoints que funcionan (autenticación OK)

* `/api/v1/accounts/1` → 200 OK
* `/api/v1/profile` → 200 OK
  Esto confirma que:
* El token es válido.
* El token pertenece a un usuario con acceso al account.

### 2.2 Recursos con datos

* Contactos: el listado funciona y devuelve datos.

  * Esto sugiere que el usuario del token **tiene visibilidad a nivel account**.

### 2.3 Recursos que fallan (resultado vacío)

* Conversaciones:

  * `/api/v1/accounts/1/conversations` → 0
  * `/api/v1/accounts/1/conversations?inbox_id=2` → 0

### 2.4 UI muestra conversaciones

* Inbox: **Whatsapp API (+5491171425098)**, id=2
* En UI se ve:

  * Pestaña “Todos”: **144**
  * “Sin asignar”: **24**
  * Se listan conversaciones y mensajes.

### 2.5 Cambio realizado por el usuario

* Se agregó el usuario como **Colaborador** en el inbox (lista de agentes visible).
* En la pantalla existe un botón **“Actualizar”** para persistir cambios.

---

## 3) Hipótesis (causas probables) — ordenadas por probabilidad

### H1 — La membresía al inbox no se guardó (falta click en “Actualizar”)

**Síntoma típico:** en la UI aparecen “seleccionados” colaboradores, pero si no se presiona **Actualizar**, no se persiste y la API sigue sin devolver conversaciones.

**Prueba:** recargar la página de colaboradores:

* Si tras recargar se perdieron los colaboradores agregados → no se guardó.

**Acción:** click “Actualizar”, recargar, y reintentar API.

---

### H2 — El token pertenece a un usuario diferente del que se agregó como colaborador

**Síntoma típico:** se agrega “Agustin Bustos” como colaborador, pero el token es de “Marcos Developer” u otro usuario técnico/admin.

**Prueba:**

* Llamar `/api/v1/profile` con el token y comparar `id/email/name` con el colaborador agregado en UI.

**Acción:** agregar como colaborador al **usuario exacto** dueño del token o regenerar token del usuario correcto.

---

### H3 — La API filtra conversaciones por asignación/estado (scope por agente)

En algunas configuraciones/versiones/roles:

* El endpoint `/conversations` devuelve solo conversaciones:

  * asignadas al agente
  * o con estados específicos (open, resolved)
  * o excluye “unassigned” según permisos/rol

**Prueba:**

* Probar API con parámetros explícitos:

  * `status=all`
  * `page=1&per_page=25`
* Asignar una conversación al usuario del token en UI y reintentar.

**Acción:** forzar parámetros en la consulta o elevar permisos/rol, o usar token de usuario con rol supervisor/admin.

---

### H4 — Diferencia de “visibilidad” UI vs API por rol/permisos

Puede ocurrir que un usuario vea el inbox en UI por permisos globales/equipo, pero el endpoint de conversaciones requiera permisos más estrictos.

**Prueba:**

* Ver `role` del usuario en `/profile` y comparar con usuario admin.
* Probar token de un admin/supervisor.

**Acción:** ajustar rol/permisos o usar token de un usuario con permisos totales.

---

## 4) Pasos de reproducción (para CODEX)

### 4.1 Reproducción del problema

1. Autenticarse con `api_access_token`.
2. Consultar:

   * `GET /api/v1/accounts/1` → 200
   * `GET /api/v1/profile` → 200
3. Consultar conversaciones:

   * `GET /api/v1/accounts/1/conversations` → `[]` / total 0
   * `GET /api/v1/accounts/1/conversations?inbox_id=2` → `[]` / total 0
4. Verificar en UI:

   * Inbox “Whatsapp API” id=2 muestra ~144 conversaciones.

### 4.2 Cambio aplicado

* En UI → Entradas → Whatsapp API → Colaboradores
* Usuario se agrega como colaborador (agentes listados).
* Aún así, API continúa devolviendo 0.

---

## 5) Plan de diagnóstico (pasos concretos y determinísticos)

### Paso A — Confirmar persistencia de colaboradores

* En UI: Entradas → Whatsapp API → Colaboradores
* Click **Actualizar**
* Recargar la página (F5)
* Confirmar que el usuario sigue listado.

**Resultado esperado:** colaboradores quedan persistidos.

---

### Paso B — Verificar identidad del token

Ejecutar:

```bash
curl -s -H "api_access_token: $TOKEN" \
"https://chatwoot.DOMINIO.com/api/v1/profile"
```

Validar:

* `id`
* `email`
* `name`
* `role` (si existe)

**Resultado esperado:** coincide con el usuario agregado como colaborador.

---

### Paso C — Probar conversaciones con query “segura”

```bash
curl -s -H "api_access_token: $TOKEN" \
"https://chatwoot.DOMINIO.com/api/v1/accounts/1/conversations?inbox_id=2&status=all&page=1&per_page=25"
```

**Interpretación:**

* Si devuelve >0 → era un filtro implícito (status/paginación).
* Si devuelve 0 → continuar con Paso D.

---

### Paso D — Validar comportamiento por asignación (si el scope es “solo assigned to me”)

1. En UI, asignar manualmente una conversación al usuario dueño del token.
2. Repetir llamada del Paso C.
3. Probar variantes:

   * `status=open`
   * `status=resolved`

**Resultado esperado:** si aparece algo solo tras asignar → API está restringida por asignación/rol.

---

## 6) Acciones recomendadas (fix)

### Fix 1 (rápido y común): guardar colaboradores

* Click **Actualizar** en Colaboradores.
* Confirmar persistencia tras recargar.

### Fix 2: token y usuario alineados

* Asegurar que el **usuario dueño del token** esté en los colaboradores del inbox.
* Si el token es de otro usuario técnico: agregar ese usuario o regenerar token.

### Fix 3: forzar consulta con status=all + paginación

* Ajustar el cliente/SDK para consultar:

  * `status=all`
  * `page/per_page`

### Fix 4: permisos/rol

* Si el endpoint limita por asignación, usar token de:

  * admin/supervisor
  * o cambiar rol/permisos del usuario del token
  * o asignar conversaciones automáticamente (“Activar asignación automática”) si lo desean.

---

## 7) Impacto

* **Automatizaciones/Reportes** que dependen de conversaciones (p. ej. `chatwoot_wa_initial_message_report`) no pueden operar.
* El sistema puede reportar falsamente “sin conversaciones” aunque el inbox esté activo.

---

## 8) Seguridad / Compliance

* Se detectó que en logs previos se imprimió un `access_token` desde `/profile`.
* Recomendaciones:

  * **Rotar el token** comprometido.
  * Sanitizar logs (no imprimir headers ni payload completo).
  * Usar variables de entorno para tokens y logging con redacción.

---

## 9) Información que CODEX necesita (inputs mínimos para cerrar)

Para resolver sin dudas, hace falta capturar (sin exponer token):

1. Salida de `/api/v1/profile` (campos: `id`, `name`, `email`, `role`).
2. Confirmación explícita: se presionó **Actualizar** y persiste tras recargar.
3. URL exacta que consulta el cliente a `/conversations` (con params, sin token).
4. (Opcional) si existe comportamiento “solo assigned-to-me”, evidencia tras asignar una conversación.

---

## 10) Estado actual

* UI: Inbox id=2 tiene ~144 conversaciones.
* API: conversaciones siguen en 0 después de agregar colaborador (pendiente verificar guardado “Actualizar” y/o mismatch de usuario del token).