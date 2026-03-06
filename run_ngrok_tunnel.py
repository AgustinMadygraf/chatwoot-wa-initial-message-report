def main() -> int:
    from src.infrastructure.settings import config
    from src.interface_adapter.controllers.ngrok_tunnel_controller import NgrokTunnelController

    config.load_env_file()
    return NgrokTunnelController().run()


if __name__ == "__main__":
    raise SystemExit(main())
