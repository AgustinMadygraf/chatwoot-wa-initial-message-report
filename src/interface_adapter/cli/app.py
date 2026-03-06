from collections.abc import Callable

import typer


def create_app(
    run_check: Callable[[], int],
    run_contacts: Callable[[], int],
    app_name: str = "chatwoot-connection-cli",
    show_about: Callable[[], None] | None = None,
    show_examples: Callable[[], None] | None = None,
) -> typer.Typer:
    app = typer.Typer(
        add_completion=False,
        no_args_is_help=False,
        rich_markup_mode="rich",
        help=(
            "Valida conectividad y autenticacion contra Chatwoot.\n\n"
            "Comandos clave:\n"
            "- [bold]check[/bold]: validacion rapida de conexion/token.\n"
            "- [bold]contacts[/bold]: reporte de una pagina de contactos."
        ),
    )

    @app.callback(invoke_without_command=True)
    def root(ctx: typer.Context) -> None:
        if ctx.invoked_subcommand is None:
            raise typer.Exit(code=run_check())

    @app.command("check")
    def check() -> None:
        """Ejecuta validacion de conectividad y token."""
        raise typer.Exit(code=run_check())

    @app.command("contacts")
    def contacts() -> None:
        """Consulta y muestra una pagina de contactos."""
        raise typer.Exit(code=run_contacts())

    @app.command("contact", hidden=True)
    def contact_alias() -> None:
        """Alias de compatibilidad para `contacts`."""
        raise typer.Exit(code=run_contacts())

    @app.command("about")
    def about() -> None:
        """Muestra informacion breve de la CLI."""
        if show_about is not None:
            show_about()
            return
        typer.echo(f"CLI: {app_name}")
        typer.echo("Comando principal: run.py check")
        typer.echo("Salida: 0 OK / 1 ERROR")

    @app.command("examples")
    def examples() -> None:
        """Muestra ejemplos de uso rapido."""
        if show_examples is not None:
            show_examples()
            return
        typer.echo("Chequeo normal: python3 run.py check")
        typer.echo("Contactos: python3 run.py contacts")
        typer.echo("Alias compatible: python3 run.py contact")
        typer.echo("Ejecucion por defecto: python3 run.py")
        typer.echo("Ayuda: python3 run.py --help")

    return app
