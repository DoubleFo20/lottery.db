import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.response import error_response

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    message = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class ValidationError(AppError):
    status_code = 400
    message = "Invalid request"


class ServiceError(AppError):
    status_code = 503
    message = "Service unavailable"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.error("AppError %s on %s %s", exc.status_code, request.method, request.url)
        payload = error_response(exc.message)
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url)
        payload = error_response("Internal server error")
        return JSONResponse(status_code=500, content=payload.model_dump())
