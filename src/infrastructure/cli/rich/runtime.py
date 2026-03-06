from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.infrastructure.cli.rich.presenters import (
    RichConnectionPresenter,
    RichContactsPresenter,
)
from src.infrastructure.requests.chatwoot_requests_gateway import ChatwootRequestsGateway
from src.infrastructure.settings.env_settings import load_chatwoot_settings
from src.interface_adapter.controllers.fetch_contacts_controller import (
    FetchContactsController,
)
from src.interface_adapter.controllers.validate_connection_controller import (
    ValidateConnectionController,
)
from src.use_case.fetch_chatwoot_contacts import FetchChatwootContactsUseCase
from src.use_case.validate_chatwoot_connection import ValidateChatwootConnectionUseCase


class RichCliRuntime:
    def __init__(self, console: Console, accent_color: str = "#009688") -> None:
        self._console = console
        self._accent_color = accent_color

    def show_about(self) -> None:
        info = Table.grid(padding=(0, 1))
        info.add_column(style="bold")
        info.add_column()
        info.add_row("CLI", "chatwoot-connection-cli")
        info.add_row("Comando principal", "python3 run.py check")
        info.add_row("Salida", "0 OK / 1 ERROR")
        self._console.print(
            Panel(
                info,
                title="[bold cyan]Info[/bold cyan]",
                border_style=self._accent_color,
            )
        )

    def show_examples(self) -> None:
        examples_table = Table(show_header=True, header_style="bold cyan")
        examples_table.add_column("Caso", style="bold")
        examples_table.add_column("Comando")
        examples_table.add_row("Chequeo normal", "python3 run.py check")
        examples_table.add_row("Contactos", "python3 run.py contacts")
        examples_table.add_row("Alias compatible", "python3 run.py contact")
        examples_table.add_row("Ejecucion por defecto", "python3 run.py")
        examples_table.add_row("Ayuda", "python3 run.py --help")
        self._console.print(
            Panel(
                examples_table,
                title="[bold cyan]Ejemplos[/bold cyan]",
                border_style=self._accent_color,
            )
        )

    def run_check(self) -> int:
        try:
            with self._console.status(
                "[cyan]Validando conexion con Chatwoot...[/cyan]", spinner="dots"
            ):
                settings = load_chatwoot_settings()
                gateway = ChatwootRequestsGateway(settings=settings)
                use_case = ValidateChatwootConnectionUseCase(gateway=gateway)
                presenter = RichConnectionPresenter(
                    console=self._console, accent_color=self._accent_color
                )
                controller = ValidateConnectionController(
                    use_case=use_case,
                    presenter=presenter,
                )
                return controller.run()
        except ValueError as exc:
            self._console.print(
                Panel(
                    f"[red]{exc}[/red]\n[yellow]Hint:[/yellow] revisa variables requeridas en .env.",
                    title="[bold red]Error de Configuracion[/bold red]",
                    border_style="red",
                )
            )
            return 1
        except Exception as exc:  # pragma: no cover
            self._console.print(
                Panel(
                    (
                        f"[red]{exc}[/red]\n"
                        "[yellow]Hint:[/yellow] ejecuta `run.py check --help` y revisa conectividad."
                    ),
                    title="[bold red]Error Inesperado[/bold red]",
                    border_style="red",
                )
            )
            return 1

    def run_contacts(self) -> int:
        try:
            with self._console.status(
                "[cyan]Consultando contactos en Chatwoot...[/cyan]", spinner="dots"
            ):
                settings = load_chatwoot_settings()
                gateway = ChatwootRequestsGateway(settings=settings)
                use_case = FetchChatwootContactsUseCase(gateway=gateway)
                presenter = RichContactsPresenter(
                    console=self._console, accent_color=self._accent_color
                )
                controller = FetchContactsController(
                    use_case=use_case,
                    presenter=presenter,
                )
                return controller.run()
        except ValueError as exc:
            self._console.print(
                Panel(
                    f"[red]{exc}[/red]\n[yellow]Hint:[/yellow] revisa variables requeridas en .env.",
                    title="[bold red]Error de Configuracion[/bold red]",
                    border_style="red",
                )
            )
            return 1
        except Exception as exc:  # pragma: no cover
            self._console.print(
                Panel(
                    (
                        f"[red]{exc}[/red]\n"
                        "[yellow]Hint:[/yellow] revisa conectividad y permisos del token."
                    ),
                    title="[bold red]Error Inesperado[/bold red]",
                    border_style="red",
                )
            )
            return 1
