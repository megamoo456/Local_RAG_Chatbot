"""
Tests for the health check endpoint.

These tests verify:
1. The endpoint exists and returns 200
2. The response schema matches HealthResponse
3. All expected services are reported

Note: In CI without Docker services, database/qdrant checks will report
errors — that's expected. The endpoint itself should still return 200
with status='unhealthy'. Full integration tests (Phase 8) will use
testcontainers for real service testing.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient) -> None:
    """Health endpoint should always return 200, even if services are down."""
    response = await client.get("/api/v1/health")
    # The endpoint should return 200 regardless of service health
    # (the health status is in the response body, not the HTTP status)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_has_required_fields(client: AsyncClient) -> None:
    """Health response should include status, environment, and services."""
    response = await client.get("/api/v1/health")
    data = response.json()

    assert "status" in data
    assert "environment" in data
    assert "services" in data
    assert data["status"] in ("healthy", "degraded", "unhealthy")


@pytest.mark.asyncio
async def test_health_reports_all_services(client: AsyncClient) -> None:
    """Health response should report on database, qdrant, and ollama."""
    response = await client.get("/api/v1/health")
    data = response.json()

    services = data["services"]
    assert "database" in services
    assert "qdrant" in services
    assert "ollama" in services

    # Each service should have a status field
    for service_name, service_health in services.items():
        assert "status" in service_health
        assert service_health["status"] in ("connected", "error")
