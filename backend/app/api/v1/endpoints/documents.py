"""
Document upload and management endpoints.
"""

import os
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.document_processor import DocumentProcessor
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])
document_processor = DocumentProcessor()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    """
    Upload a document for processing.
    
    Supported file types: pdf, docx, pptx, txt, md, html
    Maximum file size: 50MB (configurable)
    """
    settings = get_settings()
    
    # Validate file size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > settings.upload_max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.upload_max_size_mb}MB",
        )
    
    # Validate file type
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    if file_ext not in settings.allowed_extensions_set:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file_ext}' not supported. Allowed types: {', '.join(settings.allowed_extensions_set)}",
        )
    
    # Sanitize filename
    safe_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = Path(settings.upload_dir) / safe_filename
    
    # Ensure upload directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )
    
    # Create document record
    repo = DocumentRepository(session)
    document = await repo.create_document(
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file_ext,
        file_size=file_size,
    )
    
    # Process document asynchronously
    try:
        chunk_count, error_message = document_processor.process_document(
            document_id=document.id,
            file_path=str(file_path),
            file_type=file_ext,
            filename=file.filename,
        )
        
        if error_message:
            await repo.update_document_status(
                document_id=document.id,
                status=DocumentStatus.FAILED,
                error_message=error_message,
            )
        else:
            await repo.update_document_status(
                document_id=document.id,
                status=DocumentStatus.COMPLETED,
                chunk_count=chunk_count,
            )
        
        # Refresh document to get updated status
        await session.commit()
    except Exception as e:
        error_msg = f"Error during processing: {str(e)}"
        await repo.update_document_status(
            document_id=document.id,
            status=DocumentStatus.FAILED,
            error_message=error_msg,
        )
        await session.commit()
    
    # Refresh document for response
    document = await repo.get_document(document.id, current_user.id)
    return DocumentUploadResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse, status_code=status.HTTP_200_OK)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    """
    List all documents for the current user.
    """
    repo = DocumentRepository(session)
    documents, total = await repo.list_documents(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return DocumentListResponse(
        documents=[DocumentUploadResponse.model_validate(d) for d in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """
    Get a specific document by ID.
    """
    repo = DocumentRepository(session)
    document = await repo.get_document(document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a document and its file.
    """
    repo = DocumentRepository(session)
    deleted = await repo.delete_document(document_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Also delete chunks from Qdrant
    document_processor.delete_document_chunks(document_id)
    
    await session.commit()
