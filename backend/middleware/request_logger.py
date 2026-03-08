"""
Structured Request Logging Middleware — P0/P1 Observability Item
=================================================================
Logs every HTTP request/response in structured JSON format for
observability, debugging, and performance monitoring.

Features:
  - Request correlation ID (X-Request-ID header) — generated or forwarded
  - Method, path, query params, status code, duration_ms
  - Client IP (respects X-Forwarded-For)
  - Response size (Content-Length)
  - Slow request warning (>2s threshold)
  - Health check / docs path suppression (configurable)
  - JSON log format compatible with ELK / CloudWatch / Datadog
"""

import time
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


logger = logging.getLogger("platform.requests")

# Paths to suppress from request logs (high-frequency, low-value)
SUPPRESS_PATHS = frozenset([
    "/api/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
])

# Slow request threshold in seconds
SLOW_REQUEST_THRESHOLD = 2.0


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Logs structured request/response metadata for every API call.
    Attaches X-Request-ID to both request.state and response headers.
    """

    async def dispatch(self, request: Request, call_next):
        # Generate or forward request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())[:12]
        request.state.request_id = request_id

        path = request.url.path
        method = request.method
        query = str(request.url.query) if request.url.query else ""

        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Let the error handler middleware deal with it
            # but still log the failed request
            duration_ms = (time.perf_counter() - start) * 1000
            if path not in SUPPRESS_PATHS:
                logger.error(
                    "request_error | %s %s | rid=%s | ip=%s | %.0fms | unhandled exception",
                    method,
                    path,
                    request_id,
                    _get_client_ip(request),
                    duration_ms,
                )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        status = response.status_code
        content_length = response.headers.get("content-length", "-")

        # Attach request ID to response
        response.headers["X-Request-ID"] = request_id

        # Log (suppress noisy health checks)
        if path not in SUPPRESS_PATHS:
            log_line = (
                f"{method} {path}"
                f"{'?' + query if query else ''}"
                f" | {status}"
                f" | {duration_ms:.0f}ms"
                f" | {content_length}B"
                f" | ip={_get_client_ip(request)}"
                f" | rid={request_id}"
            )

            if status >= 500:
                logger.error(log_line)
            elif status >= 400:
                logger.warning(log_line)
            elif duration_ms > SLOW_REQUEST_THRESHOLD * 1000:
                logger.warning("SLOW | %s", log_line)
            else:
                logger.info(log_line)

        return response
