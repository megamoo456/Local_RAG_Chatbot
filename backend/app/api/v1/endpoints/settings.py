"""
Settings and API configuration endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.settings import (
    APIConfigCreate,
    APIConfigUpdate,
    APIConfigResponse,
    SystemSettings,
    SystemSettingsResponse,
)
from app.services.api_service import api_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/api-configs", response_model=APIConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_api_config(
    config_data: APIConfigCreate,
    current_user: User = Depends(get_current_user),
) -> APIConfigResponse:
    """
    Create a new API configuration for external services.
    """
    config_id = api_service.add_api_config(
        name=config_data.name,
        provider=config_data.provider,
        api_key=config_data.api_key,
        base_url=config_data.base_url,
        model=config_data.model,
        config=config_data.config,
    )
    
    config = api_service.get_api_config(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API configuration",
        )
    
    return APIConfigResponse(
        id=config["id"],
        name=config["name"],
        provider=config["provider"],
        base_url=config.get("base_url"),
        model=config.get("model"),
        config=config.get("config", {}),
        is_active=config["is_active"],
        created_at=config.get("created_at", ""),
    )


@router.get("/api-configs", response_model=list[APIConfigResponse], status_code=status.HTTP_200_OK)
async def list_api_configs(
    current_user: User = Depends(get_current_user),
) -> list[APIConfigResponse]:
    """
    List all API configurations.
    """
    configs = api_service.list_api_configs()
    return [
        APIConfigResponse(
            id=config["id"],
            name=config["name"],
            provider=config["provider"],
            base_url=config.get("base_url"),
            model=config.get("model"),
            config=config.get("config", {}),
            is_active=config["is_active"],
            created_at=config.get("created_at", ""),
        )
        for config in configs
    ]


@router.get("/api-configs/{config_id}", response_model=APIConfigResponse, status_code=status.HTTP_200_OK)
async def get_api_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
) -> APIConfigResponse:
    """
    Get a specific API configuration by ID.
    """
    config = api_service.get_api_config(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API configuration not found",
        )
    
    return APIConfigResponse(
        id=config["id"],
        name=config["name"],
        provider=config["provider"],
        base_url=config.get("base_url"),
        model=config.get("model"),
        config=config.get("config", {}),
        is_active=config["is_active"],
        created_at=config.get("created_at", ""),
    )


@router.put("/api-configs/{config_id}", response_model=APIConfigResponse, status_code=status.HTTP_200_OK)
async def update_api_config(
    config_id: str,
    config_data: APIConfigUpdate,
    current_user: User = Depends(get_current_user),
) -> APIConfigResponse:
    """
    Update an API configuration.
    """
    config = api_service.get_api_config(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API configuration not found",
        )
    
    if config_data.name is not None:
        config["name"] = config_data.name
    if config_data.api_key is not None:
        config["api_key"] = config_data.api_key
    if config_data.base_url is not None:
        config["base_url"] = config_data.base_url
    if config_data.model is not None:
        config["model"] = config_data.model
    if config_data.config is not None:
        config["config"] = config_data.config
    if config_data.is_active is not None:
        config["is_active"] = config_data.is_active
    
    return APIConfigResponse(
        id=config["id"],
        name=config["name"],
        provider=config["provider"],
        base_url=config.get("base_url"),
        model=config.get("model"),
        config=config.get("config", {}),
        is_active=config["is_active"],
        created_at=config.get("created_at", ""),
    )


@router.delete("/api-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete an API configuration.
    """
    deleted = api_service.delete_api_config(config_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API configuration not found",
        )


@router.get("/system", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
async def get_system_settings(
    current_user: User = Depends(get_current_user),
) -> SystemSettingsResponse:
    """
    Get system-wide settings.
    """
    return SystemSettingsResponse(
        enable_internet_search=api_service.internet_enabled,
        enable_rag=True,  # Default from config
        max_conversation_history=50,
        default_temperature=0.7,
        default_top_p=0.9,
    )


@router.put("/system", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
async def update_system_settings(
    settings_data: SystemSettings,
    current_user: User = Depends(get_current_user),
) -> SystemSettingsResponse:
    """
    Update system-wide settings.
    """
    if settings_data.enable_internet_search is not None:
        api_service.set_internet_enabled(settings_data.enable_internet_search)
    
    return SystemSettingsResponse(
        enable_internet_search=api_service.internet_enabled,
        enable_rag=settings_data.enable_rag,
        max_conversation_history=settings_data.max_conversation_history,
        default_temperature=settings_data.default_temperature,
        default_top_p=settings_data.default_top_p,
    )
