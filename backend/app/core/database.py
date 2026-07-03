"""
Async database engine and session management.

Why async SQLAlchemy?
- FastAPI is async-first; blocking DB calls would waste the event loop
- asyncpg is the fastest PostgreSQL driver for Python
- With async sessions, we can serve other requests while waiting for queries

Key patterns:
- expire_on_commit=False prevents DetachedInstanceError after commit
- Session lifecycle managed by an async context manager (get_session)
- Naming conventions ensure consistent constraint names across databases

Why not a global session?
- Sessions are NOT thread-safe or task-safe
- Each request must get its own session via dependency injection
- The session is committed/rolled back in the dependency, not in repositories
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


def create_engine(database_url: str | None = None, pool_size: int = 5):
    """
    Create an async SQLAlchemy engine.

    Args:
        database_url: Override the database URL (useful for testing).
        pool_size: Connection pool size. Use NullPool for testing.

    Returns:
        AsyncEngine instance configured for the application.
    """
    settings = get_settings()
    url = database_url or settings.database_url

    engine_kwargs = {
        "echo": settings.debug and not settings.is_production,
        "future": True,
    }

    # Use NullPool for testing to avoid connection leaks
    if settings.environment == "testing":
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["pool_size"] = pool_size
        engine_kwargs["max_overflow"] = 10
        engine_kwargs["pool_pre_ping"] = True  # Verify connections before use

    return create_async_engine(url, **engine_kwargs)


# Global engine and session factory — initialized at import time
engine = create_engine()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevents DetachedInstanceError
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.

    Usage in FastAPI endpoints:
        @router.get("/items")
        async def list_items(session: AsyncSession = Depends(get_session)):
            ...

    The session is automatically committed on success and rolled back on error.
    This keeps transaction management out of service/repository code.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_engine() -> None:
    """Dispose of the engine's connection pool. Call on application shutdown."""
    await engine.dispose()
