"""
Test fixtures for the RAG chatbot backend.

Uses httpx.AsyncClient for async API testing (the modern replacement
for TestClient when testing async FastAPI apps).

Design decisions:
- Uses the real app instance (not a separate test app) to test the actual wiring
- Overrides the database session dependency for test isolation
- In Phase 8, we'll add testcontainers for real PostgreSQL integration tests
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing API endpoints.

    Uses httpx's ASGI transport to call the FastAPI app directly
    (no actual HTTP server needed — faster and more reliable tests).
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
