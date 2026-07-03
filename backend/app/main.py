"""
FastAPI application factory.

Why an app factory?
- Configures logging, middleware, and routes in a predictable order
- Lifespan context manager handles startup/shutdown cleanly
- Easy to create test instances with different configurations
- Follows the Factory pattern — centralizes app wiring

Why lifespan over @app.on_event?
- @app.on_event("startup") is deprecated in FastAPI 0.93+
- lifespan context manager is the recommended replacement
- Provides clean resource acquisition/release semantics
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI

from app.api.middleware import setup_middleware
from app.api.v1.router import v1_router
from app.core.config import get_settings
from app.core.database import close_engine
from app.utils.logging import setup_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Runs startup logic before yield, shutdown logic after yield.
    This is where we initialize and tear down expensive resources
    (DB connections, model loading, etc.).
    """
    settings = get_settings()

    # --- Startup ---
    logger.info(
        "application_starting",
        environment=settings.environment,
        debug=settings.debug,
    )

    yield

    # --- Shutdown ---
    logger.info("application_shutting_down")
    await close_engine()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance ready to serve requests.
    """
    settings = get_settings()

    # Configure structured logging before anything else
    setup_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
    )

    app = FastAPI(
        title="Local RAG Chatbot API",
        description="Production-grade Retrieval-Augmented Generation chatbot API",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Setup middleware (CORS, error handling, request timing)
    setup_middleware(app)

    # Register API routes
    app.include_router(v1_router)

    return app


# Application instance — imported by uvicorn
app = create_app()
