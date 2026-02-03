"""
TraceBridge AI - Text Chunking Service
Handles text chunking with overlap for optimal embedding and retrieval.
"""

from typing import List, Optional
from uuid import uuid4
import logging

from app.models import Chunk, ChunkMetadata
from app.services.parser import ParsedDocument, ParsedPage

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
        start = end - chunk_overlap
        
        # Ensure we make progress
        if start <= chunks[-1] if chunks else 0:
            start = end
    
    return chunks


def chunk_document(
    doc: ParsedDocument,
    doc_id: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Chunk]:
    """
    Chunk a parsed document while preserving page metadata.
    
    Args:
        doc: ParsedDocument object
        doc_id: Unique document identifier
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
            
            chunk = Chunk(
                text=text,
                metadata=ChunkMetadata(
                    doc_id=doc_id,
                    filename=doc.filename,
                    chunk_id=chunk_id,
                    page_number=page.page_number,
                    chunk_index=chunk_index
                )
            )
            
            all_chunks.append(chunk)
            chunk_index += 1
    
    logger.info(
        f"Chunked document '{doc.filename}' (doc_id={doc_id}): "
        f"{len(all_chunks)} chunks from {len(doc.pages)} pages"
    )
    
    return all_chunks


def chunk_pages_by_page(
    pages: List[ParsedPage],
    doc_id: str,
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Chunk]:
    """
    Chunk pages while preserving page number metadata for each chunk.
    This is useful when you want to track which page each chunk came from.
    
    Args:
        pages: List of ParsedPage objects
        doc_id: Unique document identifier
        filename: Original filename
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of Chunk objects with accurate page metadata
    """
    all_chunks = []
    chunk_index = 0
    
    for page in pages:
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
            
            chunk = Chunk(
                text=text,
                metadata=ChunkMetadata(
                    doc_id=doc_id,
                    filename=filename,
                    chunk_id=chunk_id,
                    page_number=page.page_number,
                    chunk_index=chunk_index
                )
            )
            
            all_chunks.append(chunk)
            chunk_index += 1
    
    return all_chunks
