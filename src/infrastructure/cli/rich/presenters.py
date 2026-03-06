from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.entities.chatwoot_connection_result import ChatwootConnectionResult
from src.entities.chatwoot_contacts_result import ChatwootContactsResult


class RichConnectionPresenter:
    def __init__(self, console: Console, accent_color: str = "#009688") -> None:
        self._console = console
        self._accent_color = accent_color

    def present(self, result: ChatwootConnectionResult) -> int:
        status_label = "OK" if result.ok else "ERROR"
        status_color = "green" if result.ok else "red"

        summary = Table.grid(padding=(0, 1))
        summary.add_column(style="bold")
        summary.add_column()
        summary.add_row("Status", f"[{status_color}]{status_label}[/{status_color}]")
        summary.add_row("Endpoint", result.endpoint)
        if result.status_code is not None:
            summary.add_row("HTTP", str(result.status_code))

        self._console.print(
            Panel(
                summary,
                title="[bold cyan]Resultado[/bold cyan]",
                border_style=self._accent_color,
            )
        )
        self._console.print(f"[bold]Detalle:[/bold] {result.detail}")
        return 0 if result.ok else 1


class RichContactsPresenter:
    def __init__(self, console: Console, accent_color: str = "#009688") -> None:
        self._console = console
        self._accent_color = accent_color

    def present(self, result: ChatwootContactsResult) -> int:
        status_label = "OK" if result.ok else "ERROR"
        status_color = "green" if result.ok else "red"

        summary = Table.grid(padding=(0, 1))
        summary.add_column(style="bold")
        summary.add_column()
        summary.add_row("Status", f"[{status_color}]{status_label}[/{status_color}]")
        summary.add_row("Endpoint", result.endpoint)
        if result.status_code is not None:
            summary.add_row("HTTP", str(result.status_code))
        summary.add_row("Contactos", str(len(result.contacts)))

        self._console.print(
            Panel(
                summary,
                title="[bold cyan]Reporte Contactos[/bold cyan]",
                border_style=self._accent_color,
            )
        )
        self._console.print(f"[bold]Detalle:[/bold] {result.detail}")

        if result.contacts:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", no_wrap=True, width=5)
            table.add_column("Nombre", max_width=26, overflow="ellipsis")
            table.add_column("Telefono", no_wrap=True, width=16)
            table.add_column("Email", max_width=24, overflow="ellipsis")
            table.add_column("Creado", no_wrap=True, width=16)
            for row in result.contacts:
                table.add_row(
                    str(row.id),
                    row.name or "-",
                    row.phone_number or "-",
                    row.email or "-",
                    self._format_created_at(row.created_at),
                )
            self._console.print(table)
            self._console.print(
                "[cyan]Tip:[/cyan] usa `python3 run.py check` para validar conectividad/token."
            )
        else:
            self._console.print("[yellow]No hay contactos para mostrar en esta pagina.[/yellow]")

        return 0 if result.ok else 1

    @staticmethod
    def _format_created_at(raw_value: str) -> str:
        if not raw_value:
            return "-"
        if raw_value.isdigit():
            try:
                timestamp = int(raw_value)
                return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
            except (OverflowError, ValueError):
                return raw_value
        return raw_value
