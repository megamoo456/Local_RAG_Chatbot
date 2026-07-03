"""
Conversation management endpoints.
"""

import uuid
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    """
    Create a new conversation.
    """
    repo = ConversationRepository(session)
    conversation = await repo.create_conversation(
        user_id=current_user.id,
        title=conversation_data.title,
    )
    return ConversationResponse.model_validate(conversation)


@router.get("", response_model=ConversationListResponse, status_code=status.HTTP_200_OK)
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationListResponse:
    """
    List all conversations for the current user.
    """
    repo = ConversationRepository(session)
    conversations, total = await repo.list_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse, status_code=status.HTTP_200_OK)
async def get_conversation(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    """
    Get a specific conversation by ID.
    """
    repo = ConversationRepository(session)
    conversation = await repo.get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return ConversationResponse.model_validate(conversation)


@router.put("/{conversation_id}", response_model=ConversationResponse, status_code=status.HTTP_200_OK)
async def update_conversation(
    conversation_id: uuid.UUID,
    conversation_data: ConversationUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    """
    Update a conversation (title or active status).
    """
    repo = ConversationRepository(session)
    conversation = await repo.update_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        title=conversation_data.title,
        is_active=conversation_data.is_active,
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return ConversationResponse.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a conversation (soft delete).
    """
    repo = ConversationRepository(session)
    deleted = await repo.delete_conversation(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse], status_code=status.HTTP_200_OK)
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[MessageResponse]:
    """
    Get all messages in a conversation.
    """
    repo = ConversationRepository(session)
    messages = await repo.get_messages(conversation_id, current_user.id)
    return [MessageResponse.model_validate(m) for m in messages]
