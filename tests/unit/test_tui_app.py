from infrastructure.AS400.tui.app import As400App


def test_tui_app_loads() -> None:
    app = As400App()
    assert app is not None
