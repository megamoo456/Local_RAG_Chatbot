"""
Health check endpoint.

This is the first endpoint we build because:
1. Verifies the entire stack is wired correctly (FastAPI → DB → Qdrant)
2. Used by Docker health checks to determine container readiness
3. Used by load balancers to route traffic only to healthy instances
4. First thing you check when debugging "why isn't it working"

Design: Checks each dependency independently and reports per-service status.
The overall status is 'healthy' only if ALL dependencies are connected.
"""

import time

import httpx
import structlog
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.dependencies import DbSession
from app.schemas.health import HealthResponse, ServiceHealth

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health of all application dependencies.",
)
async def health_check(session: DbSession) -> HealthResponse:
    """
    Check connectivity to all critical dependencies.

    Returns per-service health with latency measurements.
    Overall status is 'healthy' only if all services are reachable.
    """
    settings = get_settings()
    services: dict[str, ServiceHealth] = {}

    # -------------------------------------------------------------------------
    # Check PostgreSQL
    # -------------------------------------------------------------------------
    try:
        start = time.perf_counter()
        await session.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start) * 1000
        services["database"] = ServiceHealth(status="connected", latency_ms=round(latency, 1))
    except Exception as e:
        logger.error("health_check_database_failed", error=str(e))
        services["database"] = ServiceHealth(status="error", error=str(e))

    # -------------------------------------------------------------------------
    # Check Qdrant
    # -------------------------------------------------------------------------
    try:
        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"http://{settings.qdrant_host}:{settings.qdrant_port}/healthz"
            )
            response.raise_for_status()
        latency = (time.perf_counter() - start) * 1000
        services["qdrant"] = ServiceHealth(status="connected", latency_ms=round(latency, 1))
    except Exception as e:
        logger.error("health_check_qdrant_failed", error=str(e))
        services["qdrant"] = ServiceHealth(status="error", error=str(e))

    # -------------------------------------------------------------------------
    # Check Ollama
    # -------------------------------------------------------------------------
    try:
        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            response.raise_for_status()
        latency = (time.perf_counter() - start) * 1000
        services["ollama"] = ServiceHealth(status="connected", latency_ms=round(latency, 1))
    except Exception as e:
        logger.warning("health_check_ollama_failed", error=str(e))
        services["ollama"] = ServiceHealth(status="error", error=str(e))

    # -------------------------------------------------------------------------
    # Determine overall status
    # -------------------------------------------------------------------------
    # Database and Qdrant are critical; Ollama degraded is acceptable (model may be loading)
    critical_services = ["database", "qdrant"]
    all_critical_healthy = all(
        services.get(s, ServiceHealth(status="error")).status == "connected"
        for s in critical_services
    )
    ollama_healthy = services.get("ollama", ServiceHealth(status="error")).status == "connected"

    if all_critical_healthy and ollama_healthy:
        overall_status = "healthy"
    elif all_critical_healthy:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        environment=settings.environment,
        services=services,
    )
