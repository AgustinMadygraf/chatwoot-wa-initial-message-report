from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.entities.chatwoot_contacts_result import ChatwootContactsResult


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
            table.add_column("ID")
            table.add_column("Nombre")
            table.add_column("Telefono")
            table.add_column("Email")
            table.add_column("Creado")
            for row in result.contacts:
                table.add_row(
                    str(row.id),
                    row.name or "-",
                    row.phone_number or "-",
                    row.email or "-",
                    row.created_at or "-",
                )
            self._console.print(table)

        return 0 if result.ok else 1
