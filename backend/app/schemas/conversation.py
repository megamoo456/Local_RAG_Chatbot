"""
Conversation-related schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    title: Optional[str] = Field(None, max_length=500, description="Optional title for the conversation")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: Optional[str] = Field(None, max_length=500, description="New title for the conversation")
    is_active: Optional[bool] = Field(None, description="Whether the conversation is active")


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: UUID = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    message_count: int = Field(..., description="Number of messages in the conversation")
    is_active: bool = Field(..., description="Whether the conversation is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for listing conversations."""

    conversations: list[ConversationResponse] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total number of conversations")


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    content: str = Field(..., min_length=1, max_length=4096, description="Message content")
    role: str = Field(..., description="Message role (user/assistant/system)")


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: UUID = Field(..., description="Message ID")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    sources: list[dict] = Field(default_factory=list, description="Citation sources")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True
