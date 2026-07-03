"""
Security utilities — authentication and authorization.

Phase 1: Single-user mode with API key authentication.
This is intentionally minimal. Full JWT auth will be added in a later phase.

Why start with API key?
- Unblocks RAG development without auth complexity
- Still prevents unauthorized access in development
- API key validation has the same interface as JWT (a dependency),
  so swapping to JWT later requires zero endpoint changes

Future (Phase 8+):
- JWT access + refresh tokens
- User registration / login endpoints
- Role-based access control (RBAC)
- Password hashing (passlib + bcrypt)
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

# API key header scheme — looks for "X-API-Key" header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """
    Validate the API key from the request header.

    In single-user mode, this compares against the configured API_KEY.
    When JWT auth is added, this dependency will be replaced by a
    token-validation dependency with the same signature.

    Args:
        api_key: The API key from the X-API-Key header.

    Returns:
        The validated API key string.

    Raises:
        HTTPException: 401 if the key is missing or invalid.
    """
    settings = get_settings()

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide it via the X-API-Key header.",
        )

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    return api_key


# Convenience dependency — use on endpoints that require authentication
# Usage: @router.get("/protected", dependencies=[Depends(require_auth)])
require_auth = Depends(verify_api_key)
