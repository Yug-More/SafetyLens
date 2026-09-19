from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def error_payload(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(code, message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        messages: list[str] = []
        for err in exc.errors():
            loc = [str(part) for part in err.get("loc", []) if part != "body"]
            field = ".".join(loc) if loc else "request"
            messages.append(f"{field}: {err.get('msg', 'Invalid value')}")
        message = "; ".join(messages) if messages else "Invalid request"
        return JSONResponse(
            status_code=422,
            content=error_payload("VALIDATION_ERROR", message),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_payload(
                "INTERNAL_ERROR",
                "An unexpected error occurred. Please try again.",
            ),
        )
