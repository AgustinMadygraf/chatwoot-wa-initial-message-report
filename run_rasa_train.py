def main() -> int:
    from src.interface_adapter.controllers.rasa_train_controller import RasaTrainController

    return RasaTrainController().run()


if __name__ == "__main__":
    raise SystemExit(main())
