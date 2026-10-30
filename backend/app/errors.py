"""Custom error types and FastAPI exception handlers for PayShield AI.

Every error response follows the envelope:
    {"error": {"code": "...", "message": "...", "details": [...]}}
"""

from __future__ import annotations

from typing import Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------
class ErrorCode:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    BAD_REQUEST = "BAD_REQUEST"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# Application exception
# ---------------------------------------------------------------------------
class AppError(Exception):
    """Raise in service/router code to produce a structured error response."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[List[Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _envelope(code: str, message: str, details: list | None = None) -> dict:
    body: dict[str, Any] = {"code": code, "message": message}
    if details:
        body["details"] = details
    return {"error": body}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
def _app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.code, exc.message, exc.details),
    )


def _validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = []
    for err in exc.errors():
        details.append(
            {
                "loc": list(err.get("loc", [])),
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            }
        )
    return JSONResponse(
        status_code=422,
        content=_envelope(ErrorCode.VALIDATION_ERROR, "Validation failed", details),
    )


def _generic_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_envelope(ErrorCode.INTERNAL_ERROR, "Internal server error"),
    )


# ---------------------------------------------------------------------------
# Register all handlers on the app
# ---------------------------------------------------------------------------
def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _generic_error_handler)  # type: ignore[arg-type]
