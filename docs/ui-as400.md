# UI/AS400 / Textual

## Filosofía
- Layout fijo de cabecera, tabla y footer para replicar green-screen CLIs.
- Navegación por teclado: *dedicated keys* (F1=Help, F3=Salir, F5=Refresh, F8/P=next, F9/N=previous, 1-4 para datasets).
- Colores: encabezados en amarillo, filas verdes, fondo oscuro.
- Accesibilidad: focus visible en la tabla y atajos numéricos para acelerar flujos.

## Pantallas
1. **Pantalla de menú** (CLI sin args): menú textual enumerado con opciones 0-6 y prompt de selección tipo “Selección: ”.
2. **Tablas AS/400**:
   - Cabecera: título + timestamp + línea de separación.
   - Columnas: anchos fijos adaptados al ancho de terminal (botones de truncado `...`).
   - Footer: barra verde con F1-F5-F8-F9, muestra página y tiempo transcurrido.
3. **Pantalla TUI Textual** (`--tui`):
   - `Header` con título.
   - `DataTable` con scroll/paginación, filas responsive al alto.
   - `Footer` con atajos y un widget `Static` para mensajes de estado.

## Navegación y shortcuts
- Teclas funcionales: `F1` ayuda, `F3` salir, `F5` refresca dataset actual, `F8`/`N` siguiente página, `F9`/`P` anterior página.
- Números: `1=cuentas`, `2=inboxes`, `3=conversaciones`, `4=mensajes`.
- `F5` reutiliza los fetchers y dispara nueva consulta a la base.
- Mensajes de estatus aparecen en la barra inferior y describen dataset + hora.

## Accesibilidad y productividad
- Incluye atajos numéricos, F-keys y paginación por altura.
- Las tablas admiten `row` focus y se actualizan sin limpiar la pantalla entera.
- Se proveen mensajes de error/estado en el footer (por ejemplo: `Listar ... fallo`).
