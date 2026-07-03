"""
Custom exception hierarchy.

Why custom exceptions?
- Maps domain errors to HTTP status codes cleanly
- Avoids scattering HTTPException throughout business logic
- Centralizes error formatting (consistent API error responses)
- Business logic raises domain exceptions; the API layer catches and translates

Pattern: Services raise domain exceptions → middleware/handlers translate to HTTP.
This keeps the service layer framework-agnostic and testable.
"""

from typing import Any


class AppError(Exception):
    """
    Base exception for all application errors.

    All custom exceptions inherit from this so we can catch
    'any app error' in a single handler.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        detail: Any = None,
    ) -> None:
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class NotFoundError(AppError):
    """Resource not found (maps to HTTP 404)."""

    def __init__(self, resource: str, identifier: Any = None) -> None:
        detail = {"resource": resource, "identifier": str(identifier)} if identifier else None
        super().__init__(
            message=f"{resource} not found" + (f": {identifier}" if identifier else ""),
            detail=detail,
        )


class ValidationError(AppError):
    """Invalid input or business rule violation (maps to HTTP 422)."""

    def __init__(self, message: str = "Validation error", errors: list[dict] | None = None) -> None:
        super().__init__(message=message, detail=errors)
        self.errors = errors


class ConflictError(AppError):
    """Resource conflict, e.g. duplicate entry (maps to HTTP 409)."""

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message=message)


class AuthenticationError(AppError):
    """Authentication failure (maps to HTTP 401)."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message=message)


class AuthorizationError(AppError):
    """Insufficient permissions (maps to HTTP 403)."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message)


class ExternalServiceError(AppError):
    """
    External service failure (maps to HTTP 502 or 503).

    Used when Ollama, Qdrant, or other external services are unreachable
    or return unexpected responses.
    """

    def __init__(self, service: str, message: str = "Service unavailable") -> None:
        super().__init__(
            message=f"{service}: {message}",
            detail={"service": service},
        )


class FileTooLargeError(ValidationError):
    """Uploaded file exceeds size limit (maps to HTTP 413)."""

    def __init__(self, max_size_mb: int, actual_size_mb: float) -> None:
        super().__init__(
            message=f"File too large: {actual_size_mb:.1f}MB exceeds {max_size_mb}MB limit"
        )


class UnsupportedFileTypeError(ValidationError):
    """Uploaded file type is not supported (maps to HTTP 415)."""

    def __init__(self, file_type: str, allowed_types: set[str]) -> None:
        super().__init__(
            message=f"Unsupported file type: .{file_type}. Allowed: {', '.join(sorted(allowed_types))}"
        )
