def main() -> int:
    from src.infrastructure.settings import config
    from src.interface_adapter.controllers.chatwoot_bridge_controller import (
        ChatwootBridgeController,
    )

    config.load_env_file()
    return ChatwootBridgeController().run()


if __name__ == "__main__":
    raise SystemExit(main())
