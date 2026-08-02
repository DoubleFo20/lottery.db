from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import AppError, NotFoundError, ValidationError, register_exception_handlers


def build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise AppError("app error")

    @app.get("/not-found")
    def not_found() -> None:
        raise NotFoundError()

    @app.get("/bad-request")
    def bad_request() -> None:
        raise ValidationError("invalid payload")

    @app.get("/unhandled")
    def unhandled() -> None:
        raise RuntimeError("kaboom")

    return app


def test_app_error_returns_standard_payload() -> None:
    with TestClient(build_app()) as client:
        response = client.get("/boom")
    assert response.status_code == 500
    assert response.json() == {"success": False, "message": "app error", "data": None}


def test_not_found_error_maps_to_404() -> None:
    with TestClient(build_app()) as client:
        response = client.get("/not-found")
    assert response.status_code == 404
    assert response.json()["success"] is False


def test_validation_error_maps_to_400() -> None:
    with TestClient(build_app()) as client:
        response = client.get("/bad-request")
    assert response.status_code == 400
    assert response.json()["message"] == "invalid payload"


def test_unhandled_error_maps_to_500() -> None:
    with TestClient(build_app(), raise_server_exceptions=False) as client:
        response = client.get("/unhandled")
    assert response.status_code == 500
    assert response.json() == {"success": False, "message": "Internal server error", "data": None}
