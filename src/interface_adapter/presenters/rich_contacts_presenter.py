from datetime import datetime

from src.entities.chatwoot_contacts_result import ChatwootContactsResult


class RichContactsPresenter:
    def present(self, result: ChatwootContactsResult) -> int:
        status_label = "OK" if result.ok else "ERROR"
        print("=== Reporte Contactos ===")
        print(f"Status: {status_label}")
        print(f"Endpoint: {result.endpoint}")
        if result.status_code is not None:
            print(f"HTTP: {result.status_code}")
        print(f"Contactos: {len(result.contacts)}")
        print(f"Detalle: {result.detail}")

        if result.contacts:
            print("ID | Nombre | Telefono | Email | Creado")
            print("-" * 72)
            for row in result.contacts:
                print(
                    f"{row.id} | "
                    f"{(row.name or '-')[:26]} | "
                    f"{(row.phone_number or '-')[:16]} | "
                    f"{(row.email or '-')[:24]} | "
                    f"{self._format_created_at(row.created_at)}"
                )
            print("Tip: usa `python3 run.py check` para validar conectividad/token.")
        else:
            print("No hay contactos para mostrar en esta pagina.")

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
