def main() -> int:
    from src.shared import config
    from src.interface_adapter.controllers.chatwoot_rasa_bridge_controller import (
        ChatwootRasaBridgeController,
    )

    config.load_env_file()
    return ChatwootRasaBridgeController().run()


if __name__ == "__main__":
    raise SystemExit(main())
