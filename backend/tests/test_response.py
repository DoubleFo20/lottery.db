from app.core.config import Settings, get_settings
from app.schemas.response import ApiResponse, error_response, ok_response


def test_settings_defaults() -> None:
    settings = get_settings()
    assert settings.app_name == "Lottery Foundation API"
    assert settings.db_path.endswith("lottery.sqlite")
    assert "http://localhost:5173" in settings.cors_origins


def test_settings_ignore_unprefixed_environment(monkeypatch) -> None:
    monkeypatch.setenv("DEBUG", "release")

    settings = Settings(_env_file=None)

    assert settings.debug is False


def test_ok_response() -> None:
    payload = ok_response({"status": "ok"})
    assert payload.success is True
    assert payload.message == "OK"
    assert payload.data == {"status": "ok"}


def test_error_response() -> None:
    payload = error_response("something broke")
    assert payload.success is False
    assert payload.message == "something broke"
    assert payload.data is None


def test_api_response_model_dump() -> None:
    payload: ApiResponse[dict[str, str]] = ApiResponse(
        success=True, message="OK", data={"status": "ok"}
    )
    assert payload.model_dump() == {"success": True, "message": "OK", "data": {"status": "ok"}}
