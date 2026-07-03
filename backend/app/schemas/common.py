"""
Common schemas used across the API.

Includes standard response envelopes, pagination, and error formats.
These ensure consistent API responses throughout the application.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """
    Base schema with common Pydantic v2 configuration.

    from_attributes=True enables ORM model → Pydantic model conversion
    via Model.model_validate(orm_object).
    """

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """Schema mixin for models with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class IDSchema(BaseSchema):
    """Schema mixin for models with UUID primary keys."""

    id: UUID


class ErrorResponse(BaseModel):
    """Standard error response format for all API errors."""

    error: str = Field(..., description="Human-readable error message")
    detail: Any = Field(default=None, description="Additional error details")
    status_code: int = Field(..., description="HTTP status code")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate the SQL OFFSET value."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response envelope."""

    items: list[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., description="Total number of items across all pages")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[T]":
        """Factory method to create a paginated response with calculated total_pages."""
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class SuccessResponse(BaseModel):
    """Standard success response for operations without return data."""

    message: str = "Operation completed successfully"
    success: bool = True
