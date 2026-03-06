# TODO

- [ ] Definir alcance de la réplica local de Chatwoot
- [ ] Definir nivel de fidelidad de la réplica
- [ ] Definir estrategia de contratos/fixtures para análisis de estructura de datos
- [x] Decisión táctica: estandarizar `run.py` con UX de CLI basada en Typer + Rich sin alterar lógica de negocio
  - Opciones consideradas: script plano con `argparse`; Typer+Rich con comandos mínimos; TUI completa.
  - Elegida: Typer+Rich con `start`/`doctor` y feedback visual (justificación: claridad, mantenibilidad y patrón idiomático en ecosistema FastAPI).
- [x] Decisión táctica: encapsular errores de arranque con mensajes accionables en CLI
  - Opciones consideradas: traceback crudo; manejo de excepción con hint; autoremediación de configuración.
  - Elegida: manejo de excepción con hint hacia `doctor` (justificación: experiencia humana sin sobre-ingeniería).
- [x] Decisión táctica: ubicar la política de fallback de puertos en el use case
  - Opciones consideradas: resolver en `run.py`; resolver en adapter uvicorn; resolver en use case con puerto de disponibilidad.
  - Elegida: use case + puerto `PortAvailabilityChecker` (justificación: reglas de aplicación en capa de casos de uso y bajo acoplamiento a infraestructura).
- [x] Decisión táctica: desacoplar controller del adapter concreto de uvicorn
  - Opciones consideradas: mantener `new Uvicorn...` en controller; inyección por constructor desde composición raíz.
  - Elegida: inyección por constructor (justificación: DIP/SOLID y testabilidad).
