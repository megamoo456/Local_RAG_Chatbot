"""
Service for managing external API configurations and internet search.
"""

import httpx
from typing import Optional, Dict, Any, List

try:
    from duckduckgo_search import DDGS
except ModuleNotFoundError:  # pragma: no cover - exercised when dependency is absent
    DDGS = None

from app.core.config import get_settings

settings = get_settings()


class APIService:
    """Service for external API integrations and internet search."""

    def __init__(self):
        """Initialize the API service."""
        self.apis: Dict[str, Dict[str, Any]] = {}
        self.internet_enabled = False

    def add_api_config(
        self,
        name: str,
        provider: str,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add an API configuration.

        Args:
            name: Display name for the API
            provider: Provider name (openai, anthropic, etc.)
            api_key: API key
            base_url: Optional base URL
            model: Optional default model
            config: Additional configuration

        Returns:
            Configuration ID
        """
        import uuid
        config_id = str(uuid.uuid4())
        
        self.apis[config_id] = {
            "id": config_id,
            "name": name,
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "config": config or {},
            "is_active": True,
        }
        
        return config_id

    def get_api_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get an API configuration by ID."""
        return self.apis.get(config_id)

    def list_api_configs(self) -> List[Dict[str, Any]]:
        """List all API configurations."""
        return list(self.apis.values())

    def delete_api_config(self, config_id: str) -> bool:
        """Delete an API configuration."""
        if config_id in self.apis:
            del self.apis[config_id]
            return True
        return False

    def set_internet_enabled(self, enabled: bool) -> None:
        """Enable or disable internet search."""
        self.internet_enabled = enabled

    async def search_internet(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform internet search using DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results with title, url, and snippet
        """
        if not self.internet_enabled:
            return []

        if DDGS is None:
            return []

        try:
            results = []
            with DDGS() as ddgs:
                for result in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                    })
            return results
        except Exception as e:
            print(f"Internet search error: {e}")
            return []

    async def call_external_api(
        self,
        config_id: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Optional[str]:
        """
        Call an external API (OpenAI, Anthropic, etc.).

        Args:
            config_id: ID of the API configuration
            messages: List of message dicts with role and content
            **kwargs: Additional parameters

        Returns:
            API response text or None if failed
        """
        config = self.get_api_config(config_id)
        if not config or not config.get("is_active"):
            return None

        provider = config["provider"].lower()
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if provider == "openai":
                    return await self._call_openai(client, config, messages, **kwargs)
                elif provider == "anthropic":
                    return await self._call_anthropic(client, config, messages, **kwargs)
                else:
                    print(f"Unsupported provider: {provider}")
                    return None
        except Exception as e:
            print(f"External API call error: {e}")
            return None

    async def _call_openai(
        self,
        client: httpx.AsyncClient,
        config: Dict[str, Any],
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Optional[str]:
        """Call OpenAI-compatible API."""
        base_url = config.get("base_url", "https://api.openai.com/v1")
        model = config.get("model", "gpt-3.5-turbo")
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": messages,
            **config.get("config", {}),
            **kwargs,
        }
        
        response = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"OpenAI API error: {response.status_code} - {response.text}")
            return None

    async def _call_anthropic(
        self,
        client: httpx.AsyncClient,
        config: Dict[str, Any],
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Optional[str]:
        """Call Anthropic API."""
        base_url = config.get("base_url", "https://api.anthropic.com")
        model = config.get("model", "claude-3-sonnet-20240229")
        
        headers = {
            "x-api-key": config["api_key"],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
        # Convert messages to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", 1024),
            **config.get("config", {}),
        }
        
        if system_message:
            payload["system"] = system_message
        
        response = await client.post(
            f"{base_url}/v1/messages",
            headers=headers,
            json=payload,
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"]
        else:
            print(f"Anthropic API error: {response.status_code} - {response.text}")
            return None


# Global instance
api_service = APIService()
