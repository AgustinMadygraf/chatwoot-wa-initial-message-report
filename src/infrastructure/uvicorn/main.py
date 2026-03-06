import typer

from src.infrastructure.rich.console_factory import create_console
from src.infrastructure.rich.runtime import RichCliRuntime
from src.interface_adapter.cli.app import create_app


def build_cli_app() -> typer.Typer:
    console = create_console()
    runtime = RichCliRuntime(console=console, accent_color="#009688")
    return create_app(
        run_check=runtime.run_check,
        run_contacts=runtime.run_contacts,
        show_about=runtime.show_about,
        show_examples=runtime.show_examples,
    )

def run_cli() -> None:
    app = build_cli_app()
    app()
