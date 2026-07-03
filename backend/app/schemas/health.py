"""
Health check schemas.

The health endpoint returns the status of all critical dependencies
so operators can quickly diagnose connectivity issues.
"""

from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    """Health status of a single dependency."""

    status: str = Field(..., description="'connected' or 'error'")
    latency_ms: float | None = Field(default=None, description="Connection latency in ms")
    error: str | None = Field(default=None, description="Error message if unhealthy")


class HealthResponse(BaseModel):
    """Aggregated health check response."""

    status: str = Field(..., description="Overall status: 'healthy' or 'degraded' or 'unhealthy'")
    environment: str = Field(..., description="Current environment (development/production)")
    version: str = Field(default="0.1.0", description="Application version")
    services: dict[str, ServiceHealth] = Field(
        ..., description="Health status of each dependency"
    )
