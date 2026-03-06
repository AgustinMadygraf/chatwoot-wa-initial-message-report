from __future__ import annotations

from src.infrastructure.cli.rich.ui import console, doctor_table, quick_help_table, welcome_panel
from src.interface_adapter.presenters.cli_app import RuntimeStatus


class RichCliView:
    def show_welcome(self) -> None:
        console.print(welcome_panel())
        console.print(quick_help_table())

    def show_launching(self) -> None:
        console.print("[#009688]Launching Chatwoot bridge[/#009688]")

    def show_preparing(self) -> None:
        console.print("[cyan]Preparing runtime and selecting available port...[/cyan]")

    def show_start_error(self, message: str) -> None:
        console.print(f"[red]Error:[/red] could not start bridge ({message}).")

    def show_start_hint(self) -> None:
        console.print("[yellow]Hint:[/yellow] run `python3 run.py doctor` to validate runtime settings.")

    def show_runtime_status(self, status: RuntimeStatus) -> None:
        console.print(doctor_table(status.host, status.port, status.reload, status.secret_set))

    def show_secret_error(self) -> None:
        console.print("[red]Error:[/red] WEBHOOK_SECRET is not configured.")

    def show_secret_hint(self) -> None:
        console.print("[yellow]Hint:[/yellow] define it in `.env` and retry `python3 run.py doctor`.")
