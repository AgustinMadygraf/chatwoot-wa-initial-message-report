import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.entities.chatwoot_contacts_result import ChatwootContactsResult, ContactRow
from src.infrastructure.cli.rich.presenters import (
    RichConnectionPresenter,
    RichContactsPresenter,
)
from src.infrastructure.requests.chatwoot_requests_gateway import ChatwootRequestsGateway
from src.infrastructure.settings.env_settings import load_chatwoot_settings
from src.interface_adapter.controllers.fetch_contacts_controller import (
    FetchContactsController,
)
from src.interface_adapter.controllers.validate_connection_controller import (
    ValidateConnectionController,
)
from src.use_case.fetch_chatwoot_contacts import FetchChatwootContactsUseCase
from src.use_case.validate_chatwoot_connection import ValidateChatwootConnectionUseCase


class RichCliRuntime:
    def __init__(self, console: Console, accent_color: str = "#009688") -> None:
        self._console = console
        self._accent_color = accent_color

    def show_about(self) -> None:
        info = Table.grid(padding=(0, 1))
        info.add_column(style="bold")
        info.add_column()
        info.add_row("CLI", "chatwoot-connection-cli")
        info.add_row("Comando principal", "python3 run.py check")
        info.add_row("Salida", "0 OK / 1 ERROR")
        self._console.print(
            Panel(
                info,
                title="[bold cyan]Info[/bold cyan]",
                border_style=self._accent_color,
            )
        )

    def show_examples(self) -> None:
        examples_table = Table(show_header=True, header_style="bold cyan")
        examples_table.add_column("Caso", style="bold")
        examples_table.add_column("Comando")
        examples_table.add_row("Chequeo normal", "python3 run.py check")
        examples_table.add_row("Contactos", "python3 run.py contacts")
        examples_table.add_row("Contactos JSON", "python3 run.py contacts --json")
        examples_table.add_row("Alias compatible", "python3 run.py contact")
        examples_table.add_row("Ejecucion por defecto", "python3 run.py")
        examples_table.add_row("Ayuda", "python3 run.py --help")
        self._console.print(
            Panel(
                examples_table,
                title="[bold cyan]Ejemplos[/bold cyan]",
                border_style=self._accent_color,
            )
        )

    def run_check(self) -> int:
        try:
            with self._console.status(
                "[cyan]Validando conexion con Chatwoot...[/cyan]", spinner="dots"
            ):
                settings = load_chatwoot_settings()
                gateway = ChatwootRequestsGateway(settings=settings)
                use_case = ValidateChatwootConnectionUseCase(gateway=gateway)
                presenter = RichConnectionPresenter(
                    console=self._console, accent_color=self._accent_color
                )
                controller = ValidateConnectionController(
                    use_case=use_case,
                    presenter=presenter,
                )
                return controller.run()
        except ValueError as exc:
            self._console.print(
                Panel(
                    f"[red]{exc}[/red]\n[yellow]Hint:[/yellow] revisa variables requeridas en .env.",
                    title="[bold red]Error de Configuracion[/bold red]",
                    border_style="red",
                )
            )
            return 1
        except Exception as exc:  # pragma: no cover
            self._console.print(
                Panel(
                    (
                        f"[red]{exc}[/red]\n"
                        "[yellow]Hint:[/yellow] revisa conectividad y permisos del token."
                    ),
                    title="[bold red]Error Inesperado[/bold red]",
                    border_style="red",
                )
            )
            return 1

    def run_contacts(
        self,
        as_json: bool = False,
        all_pages: bool = False,
        save: bool = False,
    ) -> int:
        try:
            settings = load_chatwoot_settings()
            gateway = ChatwootRequestsGateway(settings=settings)

            if not all_pages:
                if as_json:
                    return self._run_contacts_json_single_page(
                        gateway=gateway,
                        save=save,
                    )

                with self._console.status(
                    "[cyan]Consultando contactos en Chatwoot...[/cyan]", spinner="dots"
                ):
                    use_case = FetchChatwootContactsUseCase(gateway=gateway)
                    presenter = RichContactsPresenter(
                        console=self._console, accent_color=self._accent_color
                    )
                    controller = FetchContactsController(
                        use_case=use_case,
                        presenter=presenter,
                    )
                    return controller.run()

            return self._run_contacts_all_pages(
                gateway=gateway,
                as_json=as_json,
                save=save,
            )
        except ValueError as exc:
            self._console.print(
                Panel(
                    f"[red]{exc}[/red]\n[yellow]Hint:[/yellow] revisa variables requeridas en .env.",
                    title="[bold red]Error de Configuracion[/bold red]",
                    border_style="red",
                )
            )
            return 1

    def _run_contacts_json_single_page(
        self,
        gateway: ChatwootRequestsGateway,
        save: bool,
    ) -> int:
        endpoint, response, error_detail = gateway.fetch_contacts_raw_response_with_retries(
            page=1,
            max_retries=3,
            retry_delay_seconds=1.0,
            on_retry=lambda attempt: self._console.print(
                f"[yellow]Reintento {attempt}/3 en pagina 1/1...[/yellow]"
            ),
        )
        if error_detail is not None:
            self._render_api_error(error_detail)
            return 1
        assert response is not None

        body: object
        try:
            body = response.json()
        except ValueError:
            body = response.text

        output: object = {
            "endpoint": endpoint,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body,
        }

        rendered = json.dumps(output, indent=2, ensure_ascii=False)
        self._console.print(rendered, markup=False, soft_wrap=True)
        if save:
            output_path = Path("data/all_contacts.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered + "\n", encoding="utf-8")
        return 0 if 200 <= response.status_code <= 299 else 1

    def _run_contacts_all_pages(
        self,
        gateway: ChatwootRequestsGateway,
        as_json: bool,
        save: bool,
    ) -> int:
        endpoint, contacts_all, first_response, error_detail = gateway.fetch_all_contacts_raw(
            max_retries=3,
            request_delay_seconds=1.0,
            on_page_downloaded=lambda page, total: self._console.print(
                f"[cyan]Pagina {page}/{total} obtenida[/cyan]"
            ),
            on_retry=lambda page, total, attempt: self._console.print(
                f"[yellow]Reintento {attempt}/3 en pagina {page}/{total}...[/yellow]"
            ),
        )
        if error_detail is not None:
            self._render_api_error(error_detail)
            return 1
        assert first_response is not None

        total_pages = max(1, (len(contacts_all) + 14) // 15)
        self._console.print(f"[green]{len(contacts_all)} contactos obtenidos[/green]")

        output: object = contacts_all
        json_output: object = {
            "endpoint": endpoint,
            "status_code": first_response.status_code,
            "headers": dict(first_response.headers),
            "meta": {
                "count": len(contacts_all),
                "total_pages": total_pages,
            },
            "body": contacts_all,
        }

        if as_json:
            rendered = json.dumps(json_output, indent=2, ensure_ascii=False)
            self._console.print(rendered, markup=False, soft_wrap=True)
            if save:
                output_path = Path("data/all_contacts.json")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(rendered + "\n", encoding="utf-8")
            return 0

        contacts_rows = self._to_contact_rows(contacts_all)
        result = ChatwootContactsResult(
            ok=True,
            status_code=200,
            endpoint=endpoint,
            detail=f"{len(contacts_rows)} contactos obtenidos en {total_pages} paginas.",
            contacts=contacts_rows,
        )
        presenter = RichContactsPresenter(
            console=self._console, accent_color=self._accent_color
        )
        exit_code = presenter.present(result)
        if save:
            rendered = json.dumps(json_output, indent=2, ensure_ascii=False)
            output_path = Path("data/all_contacts.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered + "\n", encoding="utf-8")
        return exit_code

    @staticmethod
    def _to_contact_rows(raw_contacts: list[dict]) -> list[ContactRow]:
        rows: list[ContactRow] = []
        for item in raw_contacts:
            rows.append(
                ContactRow(
                    id=item.get("id", ""),
                    name=str(item.get("name", "") or ""),
                    phone_number=str(item.get("phone_number", "") or ""),
                    email=str(item.get("email", "") or ""),
                    created_at=str(item.get("created_at", "") or ""),
                )
            )
        return rows

    def _render_api_error(self, error_detail: str) -> None:
        self._console.print(
            Panel(
                (
                    f"[red]{error_detail}[/red]\n"
                    "[yellow]Hint:[/yellow] revisa conectividad y permisos del token."
                ),
                title="[bold red]Error API[/bold red]",
                border_style="red",
            )
        )
