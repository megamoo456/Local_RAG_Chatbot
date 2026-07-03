"""
Dependency injection providers for FastAPI.

Why DI instead of global imports?
- Testability: swap real services for mocks without monkey-patching
- Lifecycle control: resources are created/destroyed per-request or per-app
- Explicit dependencies: endpoints declare what they need
- Follows the Dependency Inversion Principle (the 'D' in SOLID)

Design decision: We use FastAPI's Depends() system rather than a DI framework
like dependency-injector. FastAPI's built-in DI is sufficient for our needs
and avoids adding another abstraction layer.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session

# Type aliases for common dependencies — makes endpoint signatures cleaner
# Usage: async def endpoint(session: DbSession, settings: AppSettings): ...

DbSession = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]

async def get_current_user(session: DbSession) -> "User":
    from sqlalchemy import select
    from app.models.user import User

    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email="default@example.com",
            display_name="Default User",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
    return user

CurrentUser = Annotated["User", Depends(get_current_user)]
