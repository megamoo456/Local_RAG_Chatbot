"""
API middleware — CORS, error handling, request timing, and request ID tracing.

Why middleware instead of per-endpoint error handling?
- DRY: Every endpoint benefits from timing and error translation
- Consistency: All errors follow the same response format
- Observability: Every request gets a unique ID for log correlation
- Separation: Endpoints focus on business logic, not cross-cutting concerns

Design: We use FastAPI's exception handlers (not Starlette middleware classes)
for error translation, and a lightweight middleware for timing + request ID.
"""

import time
import uuid

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ExternalServiceError,
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
    ValidationError,
)

logger = structlog.get_logger(__name__)

# Mapping from exception type to HTTP status code
_EXCEPTION_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ConflictError: status.HTTP_409_CONFLICT,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    FileTooLargeError: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    UnsupportedFileTypeError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
}


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware on the FastAPI application."""

    settings = get_settings()

    # -------------------------------------------------------------------------
    # CORS — must be added first (outermost middleware)
    # -------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # -------------------------------------------------------------------------
    # Request timing + request ID middleware
    # -------------------------------------------------------------------------
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        """Add request ID, log requests, and measure latency."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Bind request context to structured logger
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            latency_ms = (time.perf_counter() - start_time) * 1000

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time-Ms"] = f"{latency_ms:.1f}"

            logger.info(
                "request_completed",
                status_code=response.status_code,
                latency_ms=round(latency_ms, 1),
            )

            return response

        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "request_failed",
                error=str(exc),
                latency_ms=round(latency_ms, 1),
            )
            raise

    # -------------------------------------------------------------------------
    # Exception handlers — translate domain exceptions to HTTP responses
    # -------------------------------------------------------------------------
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle all domain exceptions with consistent error format."""
        status_code = _EXCEPTION_STATUS_MAP.get(
            type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        response = JSONResponse(
            status_code=status_code,
            content={
                "error": exc.message,
                "detail": exc.detail,
                "status_code": status_code,
            },
        )
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions — never leak stack traces to clients."""
        logger.exception("unhandled_exception", error=str(exc))
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "An internal error occurred",
                "detail": str(exc) if get_settings().debug else None,
                "status_code": 500,
            },
        )
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
