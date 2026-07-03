"""
Aggregated v1 API router.

Why versioned routes?
- Allows breaking API changes without affecting existing clients
- /api/v1/ can coexist with /api/v2/ during migration
- Industry standard (Stripe, GitHub, Twilio all version their APIs)

New endpoint modules are registered here as they're built in later phases.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, chat, conversations, documents, settings

# Create the v1 router with a common prefix and tags
v1_router = APIRouter(prefix="/api/v1")

# Register endpoint modules
v1_router.include_router(health.router)
v1_router.include_router(chat.router)
v1_router.include_router(conversations.router)
v1_router.include_router(documents.router)
v1_router.include_router(settings.router)

# Future phases will add:
# v1_router.include_router(search.router)
# v1_router.include_router(users.router)
