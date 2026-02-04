"""
TraceBridge AI - Text Chunking Service
Handles text chunking with overlap and metadata extraction.
"""

from typing import List, Optional
from uuid import uuid4
import logging

from app.models import Chunk, ChunkMetadata, DocType
from app.services.parser import ParsedDocument, ParsedPage
from app.services.metadata_extractor import extract_all_metadata

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: The text to chunk
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    # Clean the text
    text = text.strip()
    
    # If text is smaller than chunk size, return as single chunk
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Calculate end position
        end = start + chunk_size
        
        # If we're not at the end, try to break at a natural boundary
        if end < len(text):
            # Try to find a paragraph break
            para_break = text.rfind("\n\n", start, end)
            if para_break > start + chunk_size // 2:
                end = para_break + 2  # Include the newlines
            else:
                # Try to find a sentence break
                for sep in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                    sent_break = text.rfind(sep, start + chunk_size // 2, end)
                    if sent_break > start:
                        end = sent_break + len(sep)
                        break
                else:
                    # Try to find a word break
                    space = text.rfind(" ", start + chunk_size // 2, end)
                    if space > start:
                        end = space + 1
        
        # Extract the chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position, accounting for overlap
        new_start = end - chunk_overlap
        
        # Ensure we make progress (avoid infinite loop)
        if new_start <= start:
            start = end
        else:
            start = new_start
    
    return chunks


def chunk_document(
    doc: ParsedDocument,
    doc_id: str,
    device_name: Optional[str] = None,
    doc_type: DocType = "other",
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Chunk]:
    """
    Chunk a parsed document while preserving page metadata and extracting
    standards, requirement IDs, test IDs, and risk IDs.
    
    Args:
        doc: ParsedDocument object
        doc_id: Unique document identifier
        device_name: Optional device name
        doc_type: Type of document
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of Chunk objects with metadata
    """
    all_chunks = []
    chunk_index = 0
    
    for page in doc.pages:
        if not page.text or not page.text.strip():
            continue
        
        # Chunk the page text
        text_chunks = chunk_text(
            page.text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        for text in text_chunks:
            chunk_id = f"{doc_id}_chunk_{chunk_index}"
            
            # Extract metadata from chunk text
            extracted = extract_all_metadata(text)
            
            chunk = Chunk(
                text=text,
                metadata=ChunkMetadata(
                    doc_id=doc_id,
                    filename=doc.filename,
                    chunk_id=chunk_id,
                    page_number=page.page_number,
                    chunk_index=chunk_index,
                    # Extended metadata
                    device_name=device_name,
                    doc_type=doc_type,
                    standards_referenced=extracted["standards_referenced"],
                    section_heading=extracted["section_heading"],
                    requirement_ids=extracted["requirement_ids"],
                    test_case_ids=extracted["test_case_ids"],
                    risk_ids=extracted["risk_ids"],
                )
            )
            
            all_chunks.append(chunk)
            chunk_index += 1
    
    logger.info(
        f"Chunked document '{doc.filename}' (doc_id={doc_id}): "
        f"{len(all_chunks)} chunks from {len(doc.pages)} pages"
    )
    
    return all_chunks
