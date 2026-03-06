## Iteración 1 - 2026-03-06
- **Problema**: la CLI no tenía UX de help/comandos; además no arrancaba por import roto en `src/use_cases/__init__.py`.
- **Opciones consideradas**:
  - A: mantener script plano y solo corregir import.
  - B: migrar entrypoint a Typer + Rich con comandos mínimos (`start`, `doctor`) conservando lógica.
  - C: rediseño completo con múltiples grupos/subcomandos.
- **Implementado**: opción B; se corrigió `__init__.py` roto y se creó CLI con `Typer` + `Rich` sin tocar use cases de negocio.
- **Antes vs Después**: de traceback sin ayuda a `--help` estructurado con opciones/comandos visibles.

## Iteración 2 - 2026-03-06
- **Problema**: errores de startup eran técnicos y poco guiados.
- **Opciones consideradas**:
  - A: dejar traceback crudo.
  - B: envolver startup con manejo de excepción y hint accionable.
  - C: sistema de diagnóstico extenso con autoremediación.
- **Implementado**: opción B; se agregó `execute_bridge()` con mensajes en rojo/amarillo y recomendación de `doctor`.
- **Antes vs Después**: de excepción técnica directa a error legible + hint concreto.

## Iteración 3 - 2026-03-06
- **Problema**: baja consistencia visual en chequeo de runtime y detalle pobre en comandos.
- **Opciones consideradas**:
  - A: solo texto plano en `doctor`.
  - B: mantener tabla Rich con estados semánticos y descripciones de comando.
  - C: dashboard TUI completo.
- **Implementado**: opción B; comandos con descripciones claras y tabla `doctor` con estados semánticos.
- **Antes vs Después**: de salida neutra a runtime check más legible y orientado a acción.

## Estado
- **AGOTADO**: no se detectan mejoras significativas adicionales (>20% de usabilidad) sin sobrediseñar ni cambiar lógica de negocio.
