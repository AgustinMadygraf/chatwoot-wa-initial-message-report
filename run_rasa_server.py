def main() -> int:
    from src.interface_adapter.controllers.rasa_server_controller import RasaServerController

    return RasaServerController().run()


if __name__ == "__main__":
    raise SystemExit(main())
