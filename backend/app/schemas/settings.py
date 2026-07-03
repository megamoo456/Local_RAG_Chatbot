"""
Settings-related schemas for API and configuration management.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class APIConfigCreate(BaseModel):
    """Schema for creating an API configuration."""

    name: str = Field(..., min_length=1, max_length=100, description="API name (e.g., 'OpenAI', 'Anthropic')")
    provider: str = Field(..., min_length=1, max_length=50, description="Provider name")
    api_key: str = Field(..., min_length=1, description="API key")
    base_url: Optional[str] = Field(None, description="Base URL for the API")
    model: Optional[str] = Field(None, description="Default model to use")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional configuration")


class APIConfigUpdate(BaseModel):
    """Schema for updating an API configuration."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="API name")
    api_key: Optional[str] = Field(None, min_length=1, description="API key")
    base_url: Optional[str] = Field(None, description="Base URL for the API")
    model: Optional[str] = Field(None, description="Default model to use")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")
    is_active: Optional[bool] = Field(None, description="Whether the API is active")


class APIConfigResponse(BaseModel):
    """Schema for API configuration response."""

    id: str = Field(..., description="Configuration ID")
    name: str = Field(..., description="API name")
    provider: str = Field(..., description="Provider name")
    base_url: Optional[str] = Field(None, description="Base URL")
    model: Optional[str] = Field(None, description="Default model")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")
    is_active: bool = Field(..., description="Whether the API is active")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class SystemSettings(BaseModel):
    """Schema for system-wide settings."""

    enable_internet_search: bool = Field(default=False, description="Enable internet search capabilities")
    enable_rag: bool = Field(default=True, description="Enable RAG by default")
    max_conversation_history: int = Field(default=50, description="Maximum messages in conversation history")
    default_temperature: float = Field(default=0.7, description="Default LLM temperature")
    default_top_p: float = Field(default=0.9, description="Default LLM top_p")


class SystemSettingsResponse(BaseModel):
    """Schema for system settings response."""

    enable_internet_search: bool = Field(..., description="Enable internet search capabilities")
    enable_rag: bool = Field(..., description="Enable RAG by default")
    max_conversation_history: int = Field(..., description="Maximum messages in conversation history")
    default_temperature: float = Field(..., description="Default LLM temperature")
    default_top_p: float = Field(..., description="Default LLM top_p")
