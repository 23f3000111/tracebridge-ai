"""
TraceBridge AI - Pydantic Models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================
# Document Upload Models
# ============================================

class UploadResponse(BaseModel):
    """Response after uploading a document."""
    success: bool
    doc_id: str
    filename: str
    chunks_indexed: int


class DocumentMetadata(BaseModel):
    """Metadata for a stored document."""
    doc_id: str
    filename: str
    chunks_indexed: int
    uploaded_at: str  # ISO format timestamp


class DocumentListResponse(BaseModel):
    """Response containing list of all documents."""
    documents: List[DocumentMetadata]
    total_count: int


# ============================================
# Chunk Models
# ============================================

class ChunkMetadata(BaseModel):
    """Metadata for a text chunk."""
    doc_id: str
    filename: str
    chunk_id: str
    page_number: Optional[int] = None
    chunk_index: int


class Chunk(BaseModel):
    """A text chunk with its metadata."""
    text: str
    metadata: ChunkMetadata


# ============================================
# Error Models
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None


# ============================================
# Delete Response
# ============================================

class DeleteResponse(BaseModel):
    """Response after deleting a document."""
    success: bool
    doc_id: str
    message: str
    chunks_deleted: int
