from typing import Any

from app.schemas.base import BaseSchema


class ApiResponse[T](BaseSchema):
    success: bool
    message: str
    data: T | None = None


def ok_response(data: Any = None, message: str = "OK") -> ApiResponse[Any]:
    return ApiResponse(success=True, message=message, data=data)


def error_response(message: str, data: Any = None) -> ApiResponse[Any]:
    return ApiResponse(success=False, message=message, data=data)
