"""
TraceBridge AI - Query Router
Handles RAG queries and gap report generation.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.models import (
    QueryRequest,
    QueryResponse,
    GapReportRequest,
    GapReportResponse,
    ErrorResponse
)
from app.services.vector_store import query_chunks
from app.services.llm import (
    generate_grounded_answer,
    verify_answer,
    extract_citations
)
from app.services.gap_analysis import generate_gap_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Processing error"}
    }
)
async def query_documents(request: QueryRequest):
    """
    Query uploaded documents using RAG.
    
    The system will:
    1. Search for relevant chunks using semantic similarity
    2. Generate a grounded answer using only the retrieved sources
    3. Provide citations for each source used
    4. Verify the answer is properly grounded (hallucination mitigation)
    
    Optional filters:
    - doc_id: Query only a specific document
    - device_name: Query only documents for a specific device
    - doc_type: Query only specific document types (vnv, biocompatibility, etc.)
    - standard: Query only chunks referencing a specific standard (ISO 10993, etc.)
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Retrieve relevant chunks
        chunks = query_chunks(
            query=request.query,
            doc_id=request.doc_id,
            device_name=request.device_name,
            doc_type=request.doc_type,
            standard=request.standard,
            top_k=request.top_k
        )
        
        logger.info(f"Query '{request.query[:50]}...' returned {len(chunks)} chunks")
        
        # Generate grounded answer
        answer, fallback_used = generate_grounded_answer(
            query=request.query,
            chunks=chunks
        )
        
        # Verify answer grounding
        verification = verify_answer(answer, chunks)
        
        # Extract citations
        citations = extract_citations(chunks)
        
        return QueryResponse(
            success=True,
            query=request.query,
            answer=answer,
            citations=citations,
            fallback_used=fallback_used,
            verification=verification
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.post(
    "/gap-report",
    response_model=GapReportResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Processing error"}
    }
)
async def create_gap_report(request: GapReportRequest):
    """
    Generate a gap analysis report for a device.
    
    The system will:
    1. Retrieve FDA requirements for the focus area
    2. Search user documents for evidence
    3. Identify gaps where evidence is missing
    4. Generate structured remediation recommendations
    
    Focus areas:
    - V&V: Verification & Validation per IEC 62304
    - Biocomp: Biocompatibility per ISO 10993
    - Software: Software documentation
    - Risk: Risk management per ISO 14971
    - General: General device documentation
    """
    if not request.device_name or not request.device_name.strip():
        raise HTTPException(status_code=400, detail="Device name is required")
    
    try:
        # Generate gap report
        gaps = await generate_gap_report(
            device_name=request.device_name,
            focus_area=request.focus_area,
            doc_ids=request.doc_ids
        )
        
        logger.info(
            f"Generated gap report for '{request.device_name}' "
            f"({request.focus_area}): {len(gaps)} gaps found"
        )
        
        return GapReportResponse(
            success=True,
            device_name=request.device_name,
            focus_area=request.focus_area,
            gaps=gaps,
            total_gaps=len(gaps),
            generated_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating gap report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating gap report: {str(e)}"
        )
