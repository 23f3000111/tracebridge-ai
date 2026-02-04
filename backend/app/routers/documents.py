"""
TraceBridge AI - Documents Router
Handles document upload, listing, and deletion with extended metadata.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import os
import uuid
import shutil
import logging

from app.config import settings
from app.models import (
    UploadResponse,
    DocumentMetadata,
    DocumentListResponse,
    DeleteResponse,
    ErrorResponse,
    DocType
)
from app.services.parser import parse_document
from app.services.chunker import chunk_document
from app.services.vector_store import (
    index_chunks,
    list_documents,
    delete_document,
    document_exists,
    get_document_chunk_count
)
from app.services.metadata_extractor import aggregate_standards_from_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["documents"])

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension."""
    return os.path.splitext(filename)[1].lower()


def validate_file_type(filename: str) -> bool:
    """Check if file type is allowed."""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type or empty file"},
        500: {"model": ErrorResponse, "description": "Processing error"}
    }
)
async def upload_document(
    file: UploadFile = File(...),
    device_name: str = Form(..., description="Device name (e.g., HeartLink Patch Platform)"),
    doc_type: str = Form(..., description="Document type: device_description, vnv, biocompatibility, regulatory")
):
    """
    Upload a PDF or DOCX document with optional metadata.
    
    The document will be:
    1. Saved to the uploads directory
    2. Parsed to extract text
    3. Chunked with overlap and metadata extraction
    4. Indexed in the vector database
    
    Returns the document ID, chunk count, and detected metadata.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if not validate_file_type(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate doc_type
    valid_doc_types = ["device_description", "vnv", "biocompatibility", "regulatory", "other"]
    if doc_type and doc_type not in valid_doc_types:
        doc_type = "other"
    
    # Generate unique document ID
    doc_id = str(uuid.uuid4())
    
    # Ensure upload directory exists
    settings.ensure_directories()
    
    # Create file path
    extension = get_file_extension(file.filename)
    safe_filename = f"{doc_id}{extension}"
    file_path = os.path.join(settings.upload_dir, safe_filename)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved uploaded file: {file_path}")
        
        # Parse the document
        parsed_doc = parse_document(file_path)
        
        if not parsed_doc.pages:
            raise HTTPException(
                status_code=400,
                detail="Document appears to be empty or could not be parsed"
            )
        
        # Chunk the document with metadata extraction
        chunks = chunk_document(
            doc=parsed_doc,
            doc_id=doc_id,
            device_name=device_name,
            doc_type=doc_type,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text content could be extracted from the document"
            )
        
        # Aggregate detected standards
        standards_detected = aggregate_standards_from_chunks(
            [{"standards_referenced": c.metadata.standards_referenced} for c in chunks]
        )
        
        # Index chunks in vector store
        chunks_indexed = index_chunks(
            chunks=chunks,
            doc_id=doc_id,
            filename=file.filename,
            device_name=device_name,
            doc_type=doc_type
        )
        
        logger.info(
            f"Successfully processed document: {file.filename} "
            f"(doc_id={doc_id}, device={device_name}, type={doc_type}, chunks={chunks_indexed})"
        )
        
        return UploadResponse(
            success=True,
            doc_id=doc_id,
            filename=file.filename,
            device_name=device_name,
            doc_type=doc_type,
            chunks_indexed=chunks_indexed,
            standards_detected=standards_detected
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing document {file.filename}: {str(e)}")
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )
    finally:
        file.file.close()


@router.get(
    "/documents",
    response_model=DocumentListResponse
)
async def get_documents():
    """
    List all uploaded documents with metadata.
    
    Returns documents with their IDs, filenames, device names,
    doc types, chunk counts, and upload timestamps.
    """
    try:
        documents = list_documents()
        
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )


@router.delete(
    "/documents/{doc_id}",
    response_model=DeleteResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"}
    }
)
async def delete_document_endpoint(doc_id: str):
    """
    Delete a document and all its chunks.
    
    This removes the document from the vector database.
    The original uploaded file is also deleted if it exists.
    """
    try:
        # Check if document exists
        if not document_exists(doc_id):
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_id}"
            )
        
        # Delete from vector store
        chunks_deleted = delete_document(doc_id)
        
        # Try to delete original file
        for ext in ALLOWED_EXTENSIONS:
            file_path = os.path.join(settings.upload_dir, f"{doc_id}{ext}")
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        
        return DeleteResponse(
            success=True,
            doc_id=doc_id,
            message="Document deleted successfully",
            chunks_deleted=chunks_deleted
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )
