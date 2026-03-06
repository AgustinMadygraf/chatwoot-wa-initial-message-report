from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    help="Chatwoot Bridge CLI",
    rich_markup_mode="rich",
)


def run_bridge() -> int:
    from src.infrastructure.settings import config
    from src.infrastructure.network.socket_port_checker import SocketPortAvailabilityChecker
    from src.infrastructure.uvicorn.webhook_bridge_server import UvicornWebhookBridgeServer
    from src.interface_adapter.controllers.chatwoot_bridge_controller import (
        ChatwootBridgeController,
    )
    from src.use_cases.run_chatwoot_bridge_server import RunChatwootBridgeUseCase

    config.load_env_file()
    usecase = RunChatwootBridgeUseCase(
        server=UvicornWebhookBridgeServer(),
        checker=SocketPortAvailabilityChecker(),
    )
    return ChatwootBridgeController(usecase=usecase).run()


def execute_bridge(quiet: bool) -> None:
    if not quiet:
        console.print("[#009688]Launching Chatwoot bridge[/#009688]")
    try:
        with console.status("[cyan]Starting bridge...[/cyan]", spinner="dots"):
            exit_code = run_bridge()
    except Exception as exc:
        console.print(f"[red]Error:[/red] could not start bridge ({exc}).")
        console.print("[yellow]Hint:[/yellow] run `python3 run.py doctor` to validate runtime settings.")
        raise typer.Exit(code=1)
    raise typer.Exit(code=exit_code)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Reduce startup output and only run the bridge.",
    ),
) -> None:
    if ctx.invoked_subcommand is not None:
        return

    if not quiet:
        console.print(
            Panel.fit(
                "[bold cyan]Chatwoot Bridge[/bold cyan]\n"
                "[#009688]Webhook runtime for incoming messages[/#009688]",
                border_style="cyan",
                title="API CLI",
            )
        )
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_row("[cyan]Command[/cyan]", "[green]python3 run.py start[/green]")
        table.add_row("[cyan]Help[/cyan]", "[green]python3 run.py --help[/green]")
        console.print(table)

    execute_bridge(quiet=quiet)


@app.command("start", help="Start the Chatwoot webhook bridge server.")
def start(
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Reduce startup output and only run the bridge.",
    )
) -> None:
    execute_bridge(quiet=quiet)


@app.command("doctor", help="Show runtime configuration checks for bridge startup.")
def doctor() -> None:
    from src.infrastructure.settings import config

    config.load_env_file()
    secret = config.get_webhook_secret()
    info = Table(title="Runtime Check", border_style="cyan")
    info.add_column("Item", style="cyan")
    info.add_column("Status", style="green")
    secret_status = "[green]set[/green]" if secret else "[red]missing[/red]"
    reload_status = "[yellow]True[/yellow]" if config.RELOAD else "[green]False[/green]"
    info.add_row("Bridge Host", f"[cyan]{config.BRIDGE_HOST}[/cyan]")
    info.add_row("Port", f"[cyan]{config.PORT}[/cyan]")
    info.add_row("Reload", reload_status)
    info.add_row("Webhook Secret", secret_status)
    console.print(info)

    if not secret:
        console.print("[red]Error:[/red] WEBHOOK_SECRET is not configured.")
        console.print("[yellow]Hint:[/yellow] define it in `.env` and retry `python3 run.py doctor`.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
