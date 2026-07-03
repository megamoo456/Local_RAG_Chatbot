"""
Repository for conversation and message data access.
"""

import uuid
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession, Message, MessageRole


class ConversationRepository:
    """Repository for conversation-related database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        title: Optional[str] = None,
    ) -> ChatSession:
        """
        Create a new conversation session.

        Args:
            user_id: ID of the user creating the conversation
            title: Optional title for the conversation

        Returns:
            Created ChatSession instance
        """
        conversation = ChatSession(
            user_id=user_id,
            title=title or "New Chat",
        )
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[ChatSession]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user (for authorization)

        Returns:
            ChatSession instance if found, None otherwise
        """
        result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.id == conversation_id)
            .where(ChatSession.user_id == user_id)
            .options(selectinload(ChatSession.messages))
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ChatSession], int]:
        """
        List all conversations for a user.

        Args:
            user_id: ID of the user
            skip: Number of conversations to skip
            limit: Maximum number of conversations to return

        Returns:
            Tuple of (list of ChatSession, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .where(ChatSession.is_active == True)
        )
        total = len(count_result.scalars().all())

        # Get conversations
        result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .where(ChatSession.is_active == True)
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        conversations = result.scalars().all()
        return list(conversations), total

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        title: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[ChatSession]:
        """
        Update a conversation.

        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user
            title: New title (optional)
            is_active: New active status (optional)

        Returns:
            Updated ChatSession instance if found, None otherwise
        """
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title
        if is_active is not None:
            conversation.is_active = is_active

        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """
        Delete a conversation (soft delete by setting is_active=False).

        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user

        Returns:
            True if deleted, False if not found
        """
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False

        conversation.is_active = False
        await self.session.flush()
        return True

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        sources: Optional[list] = None,
    ) -> Message:
        """
        Create a new message in a conversation.

        Args:
            conversation_id: ID of the conversation
            role: Message role (user/assistant/system)
            content: Message content
            sources: Optional citation sources

        Returns:
            Created Message instance
        """
        message = Message(
            session_id=conversation_id,
            role=role,
            content=content,
            sources_json=sources,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)

        # Update message count on conversation
        await self.session.execute(
            select(ChatSession).where(ChatSession.id == conversation_id)
        )
        conversation = await self.get_conversation(conversation_id, None)
        if conversation:
            conversation.message_count += 1

        return message

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[Message]:
        """
        Get all messages in a conversation.

        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user (for authorization)

        Returns:
            List of Message instances
        """
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return []
        return conversation.messages
