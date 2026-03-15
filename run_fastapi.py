import typer

from src.infrastructure.rich.fastapi_presenter import show_server_error, show_server_info

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    rich_markup_mode="rich",
    help="Levanta la replica local de contrato de Chatwoot (FastAPI).",
)


def _serve(host: str, port: int, reload_enabled: bool) -> int:
    try:
        import uvicorn

        show_server_info(host=host, port=port, reload_enabled=reload_enabled)
        uvicorn.run(
            "src.infrastructure.fastapi_app.app:app",
            host=host,
            port=port,
            reload=reload_enabled,
        )
        return 0
    except Exception as exc:  # pragma: no cover
        show_server_error(str(exc))
        return 1


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        raise typer.Exit(code=_serve(host="127.0.0.1", port=8001, reload_enabled=False))


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Host de bind."),
    port: int = typer.Option(8001, "--port", min=1, max=65535, help="Puerto de bind."),
    reload_enabled: bool = typer.Option(
        False, "--reload", help="Recarga automatica de desarrollo."
    ),
) -> None:
    """Inicia el servidor FastAPI local."""
    raise typer.Exit(code=_serve(host=host, port=port, reload_enabled=reload_enabled))


if __name__ == "__main__":
    app()
