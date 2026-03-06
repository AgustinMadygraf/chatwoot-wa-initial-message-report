import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.infrastructure.requests.chatwoot_requests_gateway import ChatwootRequestsGateway
from src.infrastructure.settings.env_settings import load_chatwoot_settings
from src.interface_adapter.controllers.validate_connection_controller import (
    ValidateConnectionController,
)
from src.interface_adapter.presenters.rich_connection_presenter import (
    RichConnectionPresenter,
)
from src.use_case.validate_chatwoot_connection import ValidateChatwootConnectionUseCase

APP_NAME = "chatwoot-connection-cli"
ACCENT_COLOR = "#009688"
console = Console()
app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    rich_markup_mode="rich",
    help="Valida conectividad y autenticacion contra Chatwoot.",
)


def _run_validation() -> int:
    settings = load_chatwoot_settings()
    gateway = ChatwootRequestsGateway(settings=settings)
    use_case = ValidateChatwootConnectionUseCase(gateway=gateway)
    presenter = RichConnectionPresenter(console=console, accent_color=ACCENT_COLOR)
    controller = ValidateConnectionController(use_case=use_case, presenter=presenter)
    return controller.run()


def main() -> int:
    try:
        with console.status(
            "[cyan]Validando conexion con Chatwoot...[/cyan]", spinner="dots"
        ):
            return _run_validation()
    except ValueError as exc:
        console.print(
            Panel(
                f"[red]{exc}[/red]\n[yellow]Hint:[/yellow] revisa variables requeridas en .env.",
                title="[bold red]Error de Configuracion[/bold red]",
                border_style="red",
            )
        )
        return 1
    except Exception as exc:  # pragma: no cover
        console.print(
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


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        exit_code = main()
        raise typer.Exit(code=exit_code)


@app.command("check")
def check() -> None:
    """Ejecuta validacion de conectividad y token."""
    exit_code = main()
    raise typer.Exit(code=exit_code)


@app.command("about")
def about() -> None:
    """Muestra informacion breve de la CLI."""
    info = Table.grid(padding=(0, 1))
    info.add_column(style="bold")
    info.add_column()
    info.add_row("CLI", APP_NAME)
    info.add_row("Comando principal", "run.py check")
    info.add_row("Salida", "0 OK / 1 ERROR")

    console.print(
        Panel(
            info,
            title="[bold cyan]Info[/bold cyan]",
            border_style=ACCENT_COLOR,
        )
    )


@app.command("examples")
def examples() -> None:
    """Muestra ejemplos de uso rapido."""
    examples_table = Table(show_header=True, header_style="bold cyan")
    examples_table.add_column("Caso", style="bold")
    examples_table.add_column("Comando")
    examples_table.add_row("Chequeo normal", "python run.py check")
    examples_table.add_row("Ejecucion por defecto", "python run.py")
    examples_table.add_row("Ayuda", "python run.py --help")
    console.print(
        Panel(
            examples_table,
            title="[bold cyan]Ejemplos[/bold cyan]",
            border_style=ACCENT_COLOR,
        )
    )


if __name__ == "__main__":
    app()
