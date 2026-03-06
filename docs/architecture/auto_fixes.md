# Auto Fixes Arquitectónicos

## [FIX] DIP en Controller-Presenter (desacople de implementación concreta)
- **Archivo**: `src/interface_adapter/controllers/validate_connection_controller.py`
- **Problema**: el controller dependía de `ConsoleConnectionPresenter` concreto, reduciendo sustituibilidad (LSP/OCP) y acoplando la orquestación de adaptación a una implementación específica.
- **Solución**: se reemplazó el tipo concreto por `ConnectionPresenter` Protocol.
- **Breaking**: No.

## [FIX] SRP en Entry Point (`run.py`)
- **Archivo**: `run.py`
- **Problema**: `run.py` mezclaba composición root + implementación de presentación Rich (`RichConnectionPresenter`) en el mismo módulo.
- **Solución**: se extrajo la implementación Rich a `src/interface_adapter/presenters/rich_connection_presenter.py`; `run.py` ahora solo compone dependencias y ejecuta comandos.
- **Breaking**: No.

## [FIX] Contrato de Presenter explícito
- **Archivo**: `src/interface_adapter/presenters/connection_presenter.py`
- **Problema**: no había contrato explícito para presenters, dificultando sustitución y testeabilidad.
- **Solución**: se creó `ConnectionPresenter` Protocol con `present(result) -> int`.
- **Breaking**: No.

## [FIX previo consolidado] Dirección de dependencias en Use Case
- **Archivo**: `src/use_case/validate_chatwoot_connection.py`
- **Problema**: el caso de uso importaba el gateway Protocol desde `interface_adapter`, violando Clean Architecture (dependencia hacia afuera).
- **Solución**: gateway Protocol ubicado en `src/use_case/gateways/chatwoot_api_gateway.py`; use case depende de este puerto interno.
- **Breaking**: No.

## Checklist de verificación
- [x] `entities` sin imports de frameworks externos de UI/HTTP.
- [x] `use_case` sin imports de `interface_adapter` ni `infrastructure`.
- [x] Dependencias externas inyectadas por constructor en use cases.
- [x] Protocols de use case con tipos de dominio/stdlib (sin tipos de frameworks).
- [x] Typer/Rich localizados en entrypoint/adaptadores.
- [x] Requests localizado en `infrastructure`.
