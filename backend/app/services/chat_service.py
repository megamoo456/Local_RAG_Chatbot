"""
Chat service with RAG capabilities.
"""

import httpx
from typing import Optional
from uuid import UUID
from qdrant_client import QdrantClient
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import get_settings
from app.services.api_service import api_service

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
        self.api_service = api_service
        
        # LangChain LLM initialization
        self.llm = OllamaLLM(
            model=self.ollama_model,
            base_url=self.ollama_url,
            temperature=settings.llm_temperature,
        )
        
        # Ensure collection exists
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Ensure Qdrant collection exists, create if not."""
        try:
            self.qdrant_client.get_collection(settings.qdrant_collection_name)
        except Exception:
            # Collection doesn't exist, create it
            try:
                from qdrant_client.models import Distance, VectorParams
                self.qdrant_client.create_collection(
                    collection_name=settings.qdrant_collection_name,
                    vectors_config=VectorParams(
                        size=384,
                        distance=Distance.COSINE,
                    ),
                )
            except Exception as e:
                print(f"Warning: Could not create Qdrant collection: {e}")

    @property
    def ollama_model(self) -> str:
        """Get current Ollama model from settings."""
        return get_settings().ollama_model

    async def retrieve_context(self, query: str, top_k: int = 5, document_ids: Optional[list[UUID]] = None) -> list[dict]:
        """
        Retrieve relevant document chunks from Qdrant.

        Args:
            query: User query to search for
            top_k: Number of results to retrieve
            document_ids: Optional list of document IDs to filter by

        Returns:
            List of retrieved document chunks with metadata
        """
        try:
            # Ensure collection exists
            self._ensure_collection_exists()
            
            # Build filter for document IDs if provided
            query_filter = None
            if document_ids:
                query_filter = {
                    "should": [
                        {"key": "document_id", "match": {"value": str(doc_id)}}
                        for doc_id in document_ids
                    ]
                }

            # Scroll through all points with optional filter
            search_results = self.qdrant_client.scroll(
                collection_name=settings.qdrant_collection_name,
                scroll_filter=query_filter,
                limit=top_k * 3,  # Get more to allow for keyword filtering
                with_payload=True,
                with_vectors=False,
            )

            # Filter by query text relevance (simple keyword matching)
            points = search_results[0] if search_results else []
            relevant_points = []
            query_lower = query.lower()

            for point in points:
                text = point.payload.get("text", "").lower()
                # Simple relevance score based on keyword matches
                matches = sum(1 for word in query_lower.split() if word in text and len(word) > 2)
                if matches > 0:
                    relevant_points.append((point, matches))

            # Sort by relevance and limit
            relevant_points.sort(key=lambda x: x[1], reverse=True)
            contexts = []
            
            for point, score in relevant_points[:top_k]:
                contexts.append({
                    "text": point.payload.get("text", ""),
                    "metadata": point.payload.get("metadata", {}),
                    "filename": point.payload.get("filename", ""),
                    "score": score,
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
        use_internet: bool = False,
    ) -> tuple[str, str]:
        """
        Generate response using LangChain to capture thoughts.

        Returns:
            Tuple of (final_response, thoughts)
        """
        # Retrieve conversation memory
        memory_text = ""
        try:
            from app.repositories.conversation_repository import ConversationRepository
            repo = ConversationRepository()
            session = await repo.get_session_by_id(conversation_id)
            if session and session.user_memory:
                memory_text = f"\nUser Memory/Preferences:\n{session.user_memory}\n"
        except Exception as e:
            print(f"Error retrieving memory: {e}")

        # Retrieve user persona
        persona_text = ""
        try:
            from app.repositories.conversation_repository import ConversationRepository
            from app.models.user import User
            repo = ConversationRepository()
            session = await repo.get_session_by_id(conversation_id)
            if session:
                # Get user from session
                user_repo = ConversationRepository()  # This is a simplification - in reality we'd have a user repo
                # For now, we'll get the user through the session's user relationship
                if session.user:
                    persona = getattr(session.user, 'persona', None)
                    if persona:
                        persona_text = f"\nUser Persona:\n{persona}\n"
        except Exception as e:
            print(f"Error retrieving persona: {e}")

        # Build context string
        context_text = ""
        if contexts:
            context_text = "\n\nRelevant context:\n"
            for i, ctx in enumerate(contexts[:3], 1):
                context_text += f"{i}. {ctx['text']}\n"

        # Add internet search results if enabled
        internet_text = ""
        if use_internet and self.api_service.internet_enabled:
            search_results = await self.api_service.search_internet(message, max_results=3)
            if search_results:
                internet_text = "\n\nInternet search results:\n"
                for i, result in enumerate(search_results, 1):
                    internet_text += f"{i}. {result['title']}\n   URL: {result['url']}\n   {result['snippet']}\n"

        # Chain of Thought Prompt
        prompt_template = ChatPromptTemplate.from_template("""
You are a helpful AI assistant. 
First, think step-by-step about how to answer the user's request based on the provided context, user memory, and user persona. 
Then, provide the final answer.

Format your response as follows:
THOUGHTS:
<your step-by-step reasoning>

ANSWER:
<your final response>

{persona}
{memory}
{context}
{internet}

User: {message}
""")

        chain = prompt_template | self.llm | StrOutputParser()

        try:
            full_response = chain.invoke({
                "persona": persona_text,
                "memory": memory_text,
                "context": context_text,
                "internet": internet_text,
                "message": message
            })

            # Split thoughts and answer
            if "THOUGHTS:" in full_response and "ANSWER:" in full_response:
                parts = full_response.split("ANSWER:")
                thoughts = parts[0].replace("THOUGHTS:", "").strip()
                answer = parts[1].strip()
            else:
                thoughts = "Direct response generated without explicit chain-of-thought."
                answer = full_response

            return answer, thoughts

        except Exception as e:
            print(f"Generation error: {e}")
            return f"I encountered an error while generating a response: {str(e)}", str(e)

    async def refine_prompt(self, message: str) -> str:
        """
        Refine a user prompt using AI to make it more effective.
        """
        refine_template = ChatPromptTemplate.from_template("""
You are an expert prompt engineer. Your task is to rewrite the user's prompt to be more clear, 
specific, and effective for an LLM, while preserving the original intent.

User Prompt: {message}

Refined Prompt:
""")
        chain = refine_template | self.llm | StrOutputParser()
        return chain.invoke({"message": message})

    async def update_memory(self, conversation_id: str, memory_text: str) -> bool:
        """
        Update the persistent memory for a conversation.
        """
        # This is a simplified implementation. In a real app, we'd use a repository.
        # For now, we'll assume the repository handles the DB update.
        from app.repositories.conversation_repository import ConversationRepository
        repo = ConversationRepository()
        return await repo.update_session_memory(conversation_id, memory_text)

    async def chat(
        self,
        message: str,
        conversation_id: str,
        document_ids: Optional[list[UUID]] = None,
        use_rag: bool = True,
        use_internet: bool = False,
        use_persona: bool = False,
    ) -> dict:
        """
        Process a chat message with optional RAG.
        """
        # Retrieve context if RAG is enabled
        sources = []
        if use_rag:
            sources = await self.retrieve_context(message, top_k=settings.rag_rerank_top_k, document_ids=document_ids)

        # Generate response and thoughts
        response, thoughts = await self.generate_response(message, sources, conversation_id, use_internet)

        return {
            "response": response,
            "thoughts": thoughts,
            "sources": sources,
            "conversation_id": conversation_id,
            "model_used": self.ollama_model,
        }
