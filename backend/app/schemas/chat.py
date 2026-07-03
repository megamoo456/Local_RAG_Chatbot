"""
Chat-related schemas for request/response validation.
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4096, description="User message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    document_ids: Optional[list[UUID]] = Field(None, description="Optional list of document IDs to use for RAG context")
    use_rag: bool = Field(default=True, description="Whether to use RAG for context")
    use_internet: bool = Field(default=False, description="Whether to use internet search")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    response: str = Field(..., description="AI-generated response")
    sources: list[dict] = Field(default_factory=list, description="Retrieved document chunks used as context")
    conversation_id: str = Field(..., description="Conversation ID for tracking")
    model_used: str = Field(..., description="LLM model used for generation")
