from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

import typer


@dataclass(frozen=True)
class RuntimeStatus:
    host: str
    port: int
    reload: bool
    secret_set: bool


class CliView(Protocol):
    def show_welcome(self) -> None: ...
    def show_launching(self) -> None: ...
    def show_preparing(self) -> None: ...
    def show_runtime_target(self, status: RuntimeStatus) -> None: ...
    def show_interrupted(self) -> None: ...
    def show_start_error(self, message: str) -> None: ...
    def show_start_hint(self) -> None: ...
    def show_runtime_status(self, status: RuntimeStatus) -> None: ...
    def show_secret_error(self) -> None: ...
    def show_secret_hint(self) -> None: ...


def create_app(
    run_bridge: Callable[[], int],
    get_runtime_status: Callable[[], RuntimeStatus],
    view: CliView,
) -> typer.Typer:
    app = typer.Typer(
        add_completion=False,
        no_args_is_help=False,
        help="Chatwoot Bridge CLI",
        epilog=(
            "Examples:\n"
            "  python3 run.py start\n"
            "  python3 run.py start --quiet\n"
            "  python3 run.py doctor"
        ),
        rich_markup_mode="rich",
    )

    def execute_bridge(quiet: bool) -> None:
        if not quiet:
            status = get_runtime_status()
            view.show_launching()
            view.show_preparing()
            view.show_runtime_target(status)
        try:
            exit_code = run_bridge()
        except KeyboardInterrupt:
            view.show_interrupted()
            raise typer.Exit(code=130)
        except Exception as exc:
            view.show_start_error(str(exc))
            view.show_start_hint()
            raise typer.Exit(code=1)
        raise typer.Exit(code=exit_code)

    @app.callback(invoke_without_command=True)
    def main(
        ctx: typer.Context,
        quiet: bool = typer.Option(
            False,
            "--quiet",
            help="Reduce startup output and only run the bridge.",
        ),
    ) -> None:
        if ctx.invoked_subcommand is not None:
            return
        if not quiet:
            view.show_welcome()
        execute_bridge(quiet=quiet)

    @app.command("start", help="Start the Chatwoot webhook bridge server.")
    def start(
        quiet: bool = typer.Option(
            False,
            "--quiet",
            help="Reduce startup output and only run the bridge.",
        )
    ) -> None:
        execute_bridge(quiet=quiet)

    @app.command("doctor", help="Show runtime configuration checks for bridge startup.")
    def doctor() -> None:
        status = get_runtime_status()
        view.show_runtime_status(status)
        if not status.secret_set:
            view.show_secret_error()
            view.show_secret_hint()
            raise typer.Exit(code=1)

    return app
