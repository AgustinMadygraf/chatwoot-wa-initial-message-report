from rich.panel import Panel
from rich.table import Table

from src.infrastructure.rich.console_factory import create_console

ACCENT_COLOR = "#009688"


def show_server_info(host: str, port: int, reload_enabled: bool) -> None:
    console = create_console()
    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Server", "Chatwoot Local Contract Mock")
    table.add_row("URL", f"http://{host}:{port}")
    table.add_row("Reload", "on" if reload_enabled else "off")
    console.print(
        Panel(
            table,
            title="[bold cyan]FastAPI Local[/bold cyan]",
            border_style=ACCENT_COLOR,
        )
    )


def show_server_error(detail: str) -> None:
    console = create_console()
    console.print(
        Panel(
            f"[red]{detail}[/red]\n[yellow]Hint:[/yellow] revisa host/port y dependencias.",
            title="[bold red]Error de Arranque[/bold red]",
            border_style="red",
        )
    )
