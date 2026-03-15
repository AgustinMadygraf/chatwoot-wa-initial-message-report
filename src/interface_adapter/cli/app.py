from collections.abc import Callable

import typer


def create_app(
    run_check: Callable[[], int],
    run_contacts: Callable[[bool, bool, bool], int],
    app_name: str = "chatwoot-connection-cli",
    show_about: Callable[[], None] | None = None,
    show_examples: Callable[[], None] | None = None,
    run_doctor: Callable[[], int] | None = None,
    run_setup_security: Callable[[str | None, bool], int] | None = None,
) -> typer.Typer:
    app = typer.Typer(
        add_completion=False,
        no_args_is_help=False,
        rich_markup_mode="rich",
        help=(
            "Valida conectividad y autenticacion contra Chatwoot.\n\n"
            "Comandos clave:\n"
            "- [bold]check[/bold]: validacion rapida de conexion/token.\n"
            "- [bold]contacts[/bold]: reporte de una pagina de contactos.\n"
            "- [bold]doctor[/bold]: diagnostico de configuracion local.\n"
            "- [bold]setup-security[/bold]: genera PROXY_API_KEY y CA bundle."
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
    def contacts(
        as_json: bool = typer.Option(
            False,
            "--json",
            help="Muestra el JSON crudo de la respuesta de Chatwoot.",
        ),
        all_pages: bool = typer.Option(
            False,
            "--all",
            help="Descarga todas las paginas de contactos automaticamente.",
        ),
        save: bool = typer.Option(
            False,
            "--save",
            help="Guarda el resultado JSON en data/all_contacts.json.",
        ),
    ) -> None:
        """Consulta y muestra una pagina de contactos."""
        raise typer.Exit(code=run_contacts(as_json, all_pages, save))

    @app.command("contact", hidden=True)
    def contact_alias(
        as_json: bool = typer.Option(
            False,
            "--json",
            help="Muestra el JSON crudo de la respuesta de Chatwoot.",
        ),
        all_pages: bool = typer.Option(
            False,
            "--all",
            help="Descarga todas las paginas de contactos automaticamente.",
        ),
        save: bool = typer.Option(
            False,
            "--save",
            help="Guarda el resultado JSON en data/all_contacts.json.",
        ),
    ) -> None:
        """Alias de compatibilidad para `contacts`."""
        raise typer.Exit(code=run_contacts(as_json, all_pages, save))

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

    @app.command("doctor")
    def doctor() -> None:
        """Diagnostica variables requeridas y artefactos locales."""
        if run_doctor is None:
            typer.echo("Comando no disponible en esta build.", err=True)
            raise typer.Exit(code=1)
        raise typer.Exit(code=run_doctor())

    @app.command("setup-security")
    def setup_security(
        base_url: str | None = typer.Option(
            None,
            "--base-url",
            help="Base URL HTTPS de Chatwoot para intentar anexar su certificado.",
        ),
        force_ca: bool = typer.Option(
            False,
            "--force-ca",
            help="Reescribe certs/chatwoot-ca-bundle.pem desde certifi antes de anexar.",
        ),
    ) -> None:
        """Genera PROXY_API_KEY en .env y crea certs/chatwoot-ca-bundle.pem."""
        if run_setup_security is None:
            typer.echo("Comando no disponible en esta build.", err=True)
            raise typer.Exit(code=1)
        raise typer.Exit(code=run_setup_security(base_url, force_ca))

    return app
