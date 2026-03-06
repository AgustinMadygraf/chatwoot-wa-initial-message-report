from src.entities.chatwoot_connection_result import ChatwootConnectionResult


class ConsoleConnectionPresenter:
    def present(self, result: ChatwootConnectionResult) -> int:
        status = "OK" if result.ok else "ERROR"
        print(f"[{status}] endpoint={result.endpoint}")

        if result.status_code is not None:
            print(f"status_code={result.status_code}")

        print(f"detail={result.detail}")
        return 0 if result.ok else 1
