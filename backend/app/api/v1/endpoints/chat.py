"""
Chat endpoint for RAG-powered conversations.
"""

import uuid
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import asyncio

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
            document_ids=request.document_ids,
            use_rag=request.use_rag,
            use_internet=request.use_internet,
            use_persona=request.use_persona,
        )

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat request: {str(e)}",
        )


@router.post("/refine", response_model=dict, status_code=status.HTTP_200_OK)
async def refine_prompt(message: str) -> dict:
    """
    Refine a user prompt using AI.
    """
    try:
        chat_service = ChatService()
        refined = await chat_service.refine_prompt(message)
        return {"refined_message": refined}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine prompt: {str(e)}",
        )


@router.post("/memory", response_model=dict, status_code=status.HTTP_200_OK)
async def update_memory(conversation_id: str, memory: str) -> dict:
    """
    Update the persistent memory for a conversation.
    """
    try:
        chat_service = ChatService()
        success = await chat_service.update_memory(conversation_id, memory)
        return {"success": success, "message": "Memory updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update memory: {str(e)}",
        )


@router.get("/stream", tags=["chat"])
async def stream_chat(message: str, conversation_id: str, use_rag: bool = True):
    """
    Stream the AI's thoughts and response.
    """
    async def event_generator():
        chat_service = ChatService()
        # We simulate streaming by sending thoughts first, then the answer
        # In a full implementation, we'd use Ollama's streaming API
        result = await chat_service.chat(
            message=message,
            conversation_id=conversation_id,
            use_rag=use_rag,
        )

        yield f"data: {json.dumps({'type': 'thought', 'content': result['thoughts']})}\n\n"
        await asyncio.sleep(1)  # Simulate thinking time
        yield f"data: {json.dumps({'type': 'answer', 'content': result['response']})}\n\n"

    from fastapi.responses import StreamingResponse
    import json

    return StreamingResponse(event_generator(), media_type="text/event-stream")
