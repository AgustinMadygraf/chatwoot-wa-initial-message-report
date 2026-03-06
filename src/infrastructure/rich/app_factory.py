import typer
from rich.console import Console

from src.infrastructure.rich.runtime import RichCliRuntime
from src.interface_adapter.cli.app import create_app


def build_app() -> typer.Typer:
    console = Console()
    runtime = RichCliRuntime(console=console, accent_color="#009688")
    return create_app(
        run_check=runtime.run_check,
        run_contacts=runtime.run_contacts,
        show_about=runtime.show_about,
        show_examples=runtime.show_examples,
    )
