"""
TraceBridge AI - Pydantic Models
Extended with metadata for multi-device, multi-doc support.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ============================================
# Document Types
# ============================================

DocType = Literal["device_description", "vnv", "biocompatibility", "regulatory", "other"]


# ============================================
# Document Upload Models
# ============================================

class UploadResponse(BaseModel):
    """Response after uploading a document."""
    success: bool
    doc_id: str
    filename: str
    device_name: Optional[str] = None
    doc_type: DocType = "other"
    chunks_indexed: int
    standards_detected: List[str] = []


class DocumentMetadata(BaseModel):
    """Metadata for a stored document."""
    doc_id: str
    filename: str
    device_name: Optional[str] = None
    doc_type: DocType = "other"
    chunks_indexed: int
    uploaded_at: str
    standards_detected: List[str] = []


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
    # Extended metadata
    device_name: Optional[str] = None
    doc_type: DocType = "other"
    standards_referenced: List[str] = []
    section_heading: Optional[str] = None
    requirement_ids: List[str] = []
    test_case_ids: List[str] = []
    risk_ids: List[str] = []


class Chunk(BaseModel):
    """A text chunk with its metadata."""
    text: str
    metadata: ChunkMetadata


# ============================================
# Query Models
# ============================================

class QueryRequest(BaseModel):
    """Request for RAG query."""
    query: str
    doc_id: Optional[str] = None
    device_name: Optional[str] = None
    doc_type: Optional[DocType] = None
    standard: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    """Citation for an answer."""
    chunk_id: str
    page_number: Optional[int] = None
    snippet: str
    relevance_score: float = 0.0


class VerificationResult(BaseModel):
    """Verification status of the answer."""
    source_grounded: bool = True
    evidence_confirmed: bool = True
    needs_human_review: bool = False
    confidence_score: float = 1.0


class QueryResponse(BaseModel):
    """Response from RAG query."""
    success: bool = True
    query: str = ""
    answer: str
    citations: List[Citation]
    fallback_used: bool = False
    verification: Optional[VerificationResult] = None


# ============================================
# Gap Report Models
# ============================================

class GapReportRequest(BaseModel):
    """Request for gap analysis."""
    device_name: str
    focus_area: Literal["V&V", "Biocomp", "Software", "Risk", "General"]
    doc_ids: List[str] = []
    top_k: int = Field(default=8, ge=1, le=20)


class GapItem(BaseModel):
    """A single gap in the report."""
    gap_title: str
    missing_requirement: str
    severity: Literal["low", "medium", "high", "critical"]
    fda_requirement_citations: List[Citation] = []
    user_evidence_citations: List[Citation] = []
    remediation_steps: List[str]
    estimated_timeline: str = "To be determined"
    estimated_cost: str = "To be determined"


class GapReportResponse(BaseModel):
    """Response containing gap analysis."""
    success: bool = True
    device_name: str
    focus_area: str
    gaps: List[GapItem]
    total_gaps: int
    generated_at: str


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
