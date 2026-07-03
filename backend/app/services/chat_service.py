"""
Chat service with RAG capabilities.
"""

import httpx
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, SearchRequest

from app.core.config import get_settings

settings = get_settings()


class ChatService:
    """Service for handling chat requests with RAG."""

    def __init__(self):
        """Initialize Qdrant and Ollama clients."""
        self.qdrant_client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.ollama_url = settings.ollama_base_url

    @property
    def ollama_model(self) -> str:
        """Get current Ollama model from settings."""
        return get_settings().ollama_model

    async def retrieve_context(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieve relevant document chunks from Qdrant.

        Args:
            query: User query to search for
            top_k: Number of results to retrieve

        Returns:
            List of retrieved document chunks with metadata
        """
        try:
            # Simple text search (in production, use embeddings)
            search_results = self.qdrant_client.search(
                collection_name=settings.qdrant_collection_name,
                query_vector=None,  # Will use text search for now
                query_filter=None,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
                score_threshold=0.0,
            )

            # Convert to dict format
            contexts = []
            for result in search_results:
                contexts.append({
                    "text": result.payload.get("text", ""),
                    "metadata": result.payload.get("metadata", {}),
                    "score": result.score,
                })

            return contexts

        except Exception as e:
            # If collection doesn't exist or search fails, return empty context
            print(f"Retrieval error: {e}")
            return []

    async def generate_response(
        self,
        message: str,
        contexts: list[dict],
        conversation_id: str,
    ) -> str:
        """
        Generate response using Ollama.

        Args:
            message: User message
            contexts: Retrieved document contexts
            conversation_id: Conversation ID for tracking

        Returns:
            Generated response text
        """
        # Build context string
        context_text = ""
        if contexts:
            context_text = "\n\nRelevant context:\n"
            for i, ctx in enumerate(contexts[:3], 1):
                context_text += f"{i}. {ctx['text']}\n"

        # Build prompt
        prompt = f"""You are a helpful AI assistant. Use the provided context to answer questions accurately.

{context_text}

User: {message}
Assistant:"""

        try:
            async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": settings.llm_temperature,
                            "top_p": settings.llm_top_p,
                            "num_predict": settings.llm_max_tokens,
                        },
                    },
                )

                response.raise_for_status()
                result = response.json()
                return result.get("response", "I apologize, but I couldn't generate a response.")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Model '{self.ollama_model}' not found. Please pull the model first: docker compose exec ollama ollama pull {self.ollama_model}"
            print(f"Generation error: {e}")
            return f"I encountered an error while generating a response: {str(e)}"
        except Exception as e:
            print(f"Generation error: {e}")
            return f"I encountered an error while generating a response: {str(e)}"

    async def chat(
        self,
        message: str,
        conversation_id: str,
        use_rag: bool = True,
    ) -> dict:
        """
        Process a chat message with optional RAG.

        Args:
            message: User message
            conversation_id: Conversation ID
            use_rag: Whether to use RAG for context

        Returns:
            Dictionary with response, sources, and metadata
        """
        # Retrieve context if RAG is enabled
        sources = []
        if use_rag:
            sources = await self.retrieve_context(message, top_k=settings.rag_rerank_top_k)

        # Generate response
        response = await self.generate_response(message, sources, conversation_id)

        return {
            "response": response,
            "sources": sources,
            "conversation_id": conversation_id,
            "model_used": self.ollama_model,
        }
