from interface_adapter.controllers.cli import main
from shared.config import load_env_file


def run() -> None:
    load_env_file()
    main()


if __name__ == "__main__":
    run()
