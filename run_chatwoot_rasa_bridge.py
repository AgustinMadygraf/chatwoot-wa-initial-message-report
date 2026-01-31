def main() -> int:
    from src.interface_adapter.controllers.chatwoot_rasa_bridge_controller import (
        ChatwootRasaBridgeController,
    )

    return ChatwootRasaBridgeController().run()


if __name__ == "__main__":
    raise SystemExit(main())
