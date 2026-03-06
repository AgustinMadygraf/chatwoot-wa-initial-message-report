from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def welcome_panel() -> Panel:
    return Panel.fit(
        "[bold cyan]Chatwoot Bridge[/bold cyan]\n"
        "[#009688]Webhook runtime for incoming messages[/#009688]",
        border_style="cyan",
        title="API CLI",
    )


def quick_help_table() -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("[cyan]Command[/cyan]", "[green]python3 run.py start[/green]")
    table.add_row("[cyan]Help[/cyan]", "[green]python3 run.py --help[/green]")
    return table


def doctor_table(host: str, port: int, reload: bool, secret_set: bool) -> Table:
    info = Table(title="Runtime Check", border_style="cyan")
    info.add_column("Item", style="cyan")
    info.add_column("Status", style="green")
    secret_status = "[green]set[/green]" if secret_set else "[red]missing[/red]"
    reload_status = "[yellow]True[/yellow]" if reload else "[green]False[/green]"
    info.add_row("Bridge Host", f"[cyan]{host}[/cyan]")
    info.add_row("Port", f"[cyan]{port}[/cyan]")
    info.add_row("Reload", reload_status)
    info.add_row("Webhook Secret", secret_status)
    return info
