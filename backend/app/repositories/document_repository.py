"""
Repository for document data access.
"""

import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document, DocumentStatus


class DocumentRepository:
    """Repository for document-related database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
        self.settings = get_settings()

    async def create_document(
        self,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
    ) -> Document:
        """
        Create a new document record.

        Args:
            user_id: ID of the user uploading the document
            filename: Original filename
            file_path: Path to the stored file
            file_type: File extension
            file_size: File size in bytes

        Returns:
            Created Document instance
        """
        document = Document(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            status=DocumentStatus.PENDING,
        )
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def get_document(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            document_id: ID of the document
            user_id: ID of the user (for authorization)

        Returns:
            Document instance if found, None otherwise
        """
        result = await self.session.execute(
            select(Document)
            .where(Document.id == document_id)
            .where(Document.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Document], int]:
        """
        List all documents for a user.

        Args:
            user_id: ID of the user
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            Tuple of (list of Document, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(Document).where(Document.user_id == user_id)
        )
        total = len(count_result.scalars().all())

        # Get documents
        result = await self.session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = result.scalars().all()
        return list(documents), total

    async def update_document_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[Document]:
        """
        Update document processing status.

        Args:
            document_id: ID of the document
            status: New status
            chunk_count: Number of chunks generated (optional)
            error_message: Error message if failed (optional)
            metadata: Extracted metadata (optional)

        Returns:
            Updated Document instance if found, None otherwise
        """
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            return None

        document.status = status
        if chunk_count is not None:
            document.chunk_count = chunk_count
        if error_message is not None:
            document.error_message = error_message
        if metadata is not None:
            document.metadata_json = metadata

        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def delete_document(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """
        Delete a document and its file.

        Args:
            document_id: ID of the document
            user_id: ID of the user

        Returns:
            True if deleted, False if not found
        """
        document = await self.get_document(document_id, user_id)
        if not document:
            return False

        # Delete the file from disk
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        await self.session.delete(document)
        await self.session.flush()
        return True
