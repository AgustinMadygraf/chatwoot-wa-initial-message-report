# Violaciones Arquitectónicas Estratégicas

No se detectaron violaciones estratégicas activas en el estado actual del código.

## Riesgos residuales (no bloqueantes)
- `run.py` continúa como composition root + comandos CLI (aceptable para este tamaño de proyecto).
- Existe `ConsoleConnectionPresenter` legacy en `src/interface_adapter/presenters/console_presenter.py`; no rompe arquitectura, pero podría retirarse si no se usa para reducir superficie.
