from src.interface_adapter.presenters.webhook_api import app


def test_webhook_route_registered():
    routes = {getattr(route, "path", None) for route in app.routes}
    assert "/webhook/{secret}" in routes
