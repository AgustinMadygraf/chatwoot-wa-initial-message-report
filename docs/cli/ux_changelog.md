## Iteracion 1 - 2026-03-06
- **Problema**: `run.py` no tenia experiencia CLI real (`--help` fallaba) y la salida era plana con `print()`.
- **Opciones consideradas**: A) mantener script y solo mejorar strings; B) migrar entrypoint a Typer + Rich preservando flujo existente; C) rediseñar con subcomandos nuevos y arquitectura UI separada completa.
- **Implementado**: opcion B. Se agrego `Typer` con comandos `check`/`about`, ejecucion por defecto compatible (`python run.py`), spinner de estado, panel Rich para resultado y tabla de resumen.
- **Antes vs Despues**: antes habia traceback o texto plano sin jerarquia; despues hay comandos descubiertos por `--help` y salida estructurada con color semantico.

## Iteracion 2 - 2026-03-06
- **Problema**: errores de configuracion mostraban excepciones tecnicas (poca accionabilidad para usuario).
- **Opciones consideradas**: A) atrapar solo `ValueError` y mostrar una linea; B) paneles de error amigables con hint contextual; C) sistema completo de codigos de error + telemetria.
- **Implementado**: opcion B. `main()` ahora captura `ValueError` y errores inesperados, imprime panel rojo con mensaje humano y hint de resolucion.
- **Antes vs Despues**: antes un error como `CHATWOOT_ACCOUNT_ID` invalido terminaba con traceback; despues muestra `Error de Configuracion` con recomendacion concreta.

## Iteracion 3 - 2026-03-06
- **Problema**: onboarding mejoro, pero faltaban ejemplos directos de uso para acelerar descubribilidad.
- **Opciones consideradas**: A) agregar ejemplos en README solamente; B) agregar comando `examples` y enriquecer `about`; C) asistente interactivo guiado.
- **Implementado**: opcion B. Se incorporo `examples` con tabla Rich de comandos frecuentes y `about` con tabla compacta (CLI/comando principal/salida).
- **Antes vs Despues**: antes el usuario debia inferir como usar la CLI; despues tiene ejemplos ejecutables desde la propia CLI sin salir del terminal.

## Iteracion 4 - 2026-03-06
- **Problema**: inconsistencia de nombrado y descubribilidad: `contact` fallaba aunque la accion existia como `contacts`.
- **Opciones consideradas**: A) documentar mejor y mantener solo `contacts`; B) agregar alias de compatibilidad `contact` + mejorar bloque de ayuda; C) renombrar comandos de forma global.
- **Implementado**: opcion B. Se agrego comando alias `contact` que ejecuta el mismo flujo, y se enriquecio el `help` principal con comandos clave para reducir friccion de onboarding.
- **Antes vs Despues**: antes `python run.py contact` devolvia error de comando inexistente; despues funciona y guia al usuario con una ayuda mas orientada.

## Iteracion 5 - 2026-03-06
- **Problema**: legibilidad baja en reporte de contactos por fechas en timestamp epoch y falta de guidance posterior al resultado.
- **Opciones consideradas**: A) dejar timestamp crudo y confiar en usuario tecnico; B) formatear fecha en presenter + tip contextual; C) agregar transformaciones en capa de dominio.
- **Implementado**: opcion B. Se formatea `created_at` a `YYYY-MM-DD HH:MM` en presenter Rich y se agrega tip de continuidad (`run.py check`), sin tocar casos de uso ni gateways.
- **Antes vs Despues**: antes la columna `Creado` era cruda (`1768006395`); despues es legible y accionable para auditoria operativa.

## Iteracion 6 - 2026-03-06
- **Problema**: tabla de contactos con demasiado ruido vertical por columnas textuales largas.
- **Opciones consideradas**: A) mantener autosizing por defecto; B) controlar anchos/no-wrap en columnas clave para escaneo rapido; C) paginado interactivo completo.
- **Implementado**: opcion B. Se ajustaron anchos y no-wrap de columnas (`ID`, `Telefono`, `Creado`) y limites visuales en texto para mejorar escaneo en terminal.
- **Antes vs Despues**: antes el listado era menos escaneable en terminal angosta; despues mantiene estructura mas compacta y consistente.

## Iteracion 7 - 2026-03-06
- **Problema**: feedback de ejecucion insuficiente en operaciones con I/O (`check` y `contacts`) desde el composition root.
- **Opciones consideradas**: A) texto estatico de "cargando"; B) spinner `console.status` + paneles de error Rich; C) progress bars completas por etapa.
- **Implementado**: opcion B. Se agregaron spinners en `run.py` para `run_check` y `run_contacts`, y manejo de errores con `Panel` rojo + hint amarillo.
- **Antes vs Despues**: antes la ejecucion era silenciosa hasta el resultado; despues hay feedback continuo y errores mas humanos.

## Iteracion 8 - 2026-03-06
- **Problema**: `about` y `examples` tenian baja jerarquia visual (salida plana) tras desacoplar capas.
- **Opciones consideradas**: A) mejorar copy manteniendo `echo`; B) inyectar renderizadores de UI en `create_app` y pintar con Rich desde `run.py`; C) volver a acoplar toda la CLI con infraestructura.
- **Implementado**: opcion B. `create_app` acepta `show_about` y `show_examples` opcionales; `run.py` renderiza paneles/tablas Rich sin romper separacion de capas.
- **Antes vs Despues**: antes habia lineas planas; despues hay paneles consistentes con la estetica FastAPI.

## Iteracion 9 - 2026-03-06
- **Problema**: `--help` tenia clutter por alias operativo (`contact`) visible junto a `contacts`.
- **Opciones consideradas**: A) eliminar alias (rompe compatibilidad); B) ocultar alias del help manteniendolo funcional; C) dejar ambos visibles.
- **Implementado**: opcion B. El comando `contact` sigue activo pero oculto con `hidden=True`.
- **Antes vs Despues**: antes el listado de comandos mostraba ruido innecesario; despues prioriza comandos canonicos sin perder backward compatibility.
