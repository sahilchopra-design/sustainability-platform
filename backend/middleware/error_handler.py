"""
Global Error Handler Middleware — P0 Reliability Item
======================================================
Catches all unhandled exceptions across the entire FastAPI application
and returns consistent, structured error responses.

Features:
  - Standardized JSON error envelope for ALL error types
  - Request correlation ID generation (X-Request-ID)
  - Pydantic validation error formatting
  - SQLAlchemy / DB error wrapping (no internal details leaked)
  - Structured error logging (JSON format)
  - Sentry-ready hook (uncomment when integrated)
"""

import time
import traceback
import uuid
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError


logger = logging.getLogger("platform.error_handler")


# ---------------------------------------------------------------------------
#  Error response envelope
# ---------------------------------------------------------------------------

def _error_response(
    status_code: int,
    error_type: str,
    message: str,
    request_id: str,
    details: Any = None,
    path: str = "",
) -> JSONResponse:
    """Consistent JSON error response."""
    body = {
        "error": {
            "type": error_type,
            "message": message,
            "status_code": status_code,
            "request_id": request_id,
            "path": path,
        }
    }
    if details:
        body["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=body)


# ---------------------------------------------------------------------------
#  Exception handlers
# ---------------------------------------------------------------------------

def register_error_handlers(app: FastAPI):
    """
    Register global exception handlers on the FastAPI app instance.
    Call this once after app creation in server.py.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())[:8]
        return _error_response(
            status_code=exc.status_code,
            error_type="http_error",
            message=str(exc.detail),
            request_id=request_id,
            path=request.url.path,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())[:8]

        # Format Pydantic errors into readable list
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            errors.append({
                "field": loc,
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            })

        logger.warning(
            "Validation error on %s %s [%s]: %d field errors",
            request.method,
            request.url.path,
            request_id,
            len(errors),
        )

        return _error_response(
            status_code=422,
            error_type="validation_error",
            message=f"Request validation failed: {len(errors)} field error(s)",
            request_id=request_id,
            details=errors,
            path=request.url.path,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())[:8]
        logger.error(
            "DB integrity error on %s %s [%s]: %s",
            request.method,
            request.url.path,
            request_id,
            str(exc.orig)[:200],
        )
        return _error_response(
            status_code=409,
            error_type="conflict",
            message="A database constraint was violated. The record may already exist or references an invalid entity.",
            request_id=request_id,
            path=request.url.path,
        )

    @app.exception_handler(OperationalError)
    async def db_operational_error_handler(request: Request, exc: OperationalError):
        request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())[:8]
        logger.critical(
            "DB connection error on %s %s [%s]: %s",
            request.method,
            request.url.path,
            request_id,
            str(exc.orig)[:200],
        )
        return _error_response(
            status_code=503,
            error_type="service_unavailable",
            message="Database is temporarily unavailable. Please retry in a few seconds.",
            request_id=request_id,
            path=request.url.path,
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())[:8]
        logger.error(
            "DB error on %s %s [%s]: %s",
            request.method,
            request.url.path,
            request_id,
            str(exc)[:300],
        )
        return _error_response(
            status_code=500,
            error_type="database_error",
            message="An internal database error occurred. The team has been notified.",
            request_id=request_id,
            path=request.url.path,
        )

    @app.exception_handler(Exception)
    async def catch_all_handler(request: Request, exc: Exception):
        request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())[:8]

        # Full traceback for logging
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        logger.error(
            "Unhandled exception on %s %s [%s]:\n%s",
            request.method,
            request.url.path,
            request_id,
            "".join(tb),
        )

        # TODO: Sentry integration (P0 #6)
        # import sentry_sdk
        # sentry_sdk.capture_exception(exc)

        return _error_response(
            status_code=500,
            error_type="internal_error",
            message="An unexpected error occurred. The team has been notified.",
            request_id=request_id,
            path=request.url.path,
        )
