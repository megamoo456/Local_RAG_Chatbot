"""
Document-related schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    id: UUID = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for listing documents."""

    documents: list[DocumentUploadResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")


class DocumentResponse(BaseModel):
    """Schema for document details."""

    id: UUID = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Processing status")
    chunk_count: int = Field(..., description="Number of chunks generated")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Optional[dict] = Field(None, description="Extracted document metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
