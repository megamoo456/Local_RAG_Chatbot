"""
Chat endpoint for RAG-powered conversations.
"""

import uuid
from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message with optional RAG context.

    This endpoint:
    - Accepts a user message
    - Optionally retrieves relevant document chunks from Qdrant
    - Generates a response using Ollama
    - Returns the response with source citations
    """
    try:
        # Generate or use provided conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Create fresh service instance to get current settings
        chat_service = ChatService()

        # Process chat with RAG
        result = await chat_service.chat(
            message=request.message,
            conversation_id=conversation_id,
            use_rag=request.use_rag,
        )

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat request: {str(e)}",
        )
