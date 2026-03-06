from src.entities.chatwoot_connection_result import ChatwootConnectionResult


class RichConnectionPresenter:
    def present(self, result: ChatwootConnectionResult) -> int:
        status_label = "OK" if result.ok else "ERROR"
        print("=== Resultado ===")
        print(f"Status: {status_label}")
        print(f"Endpoint: {result.endpoint}")
        if result.status_code is not None:
            print(f"HTTP: {result.status_code}")
        print(f"Detalle: {result.detail}")
        return 0 if result.ok else 1
