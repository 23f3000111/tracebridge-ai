"""
TraceBridge AI - Vector Store Service
Enhanced with extended metadata support for filtering.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import os
import pickle

from app.config import settings
from app.models import Chunk, DocumentMetadata, DocType
from app.services.embeddings import get_embeddings, get_embedding

logger = logging.getLogger(__name__)


class SimpleVectorStore:
    """Enhanced in-memory vector store with metadata filtering."""
    
    def __init__(self, persist_path: str):
        self.persist_path = persist_path
        self.documents: Dict[str, str] = {}  # id -> text
        self.embeddings: Dict[str, List[float]] = {}  # id -> embedding
        self.metadatas: Dict[str, Dict[str, Any]] = {}  # id -> metadata
        self._load()
    
    def _load(self):
        """Load persisted data if exists."""
        data_file = os.path.join(self.persist_path, "vector_store.pkl")
        if os.path.exists(data_file):
            try:
                with open(data_file, "rb") as f:
                    data = pickle.load(f)
                    self.documents = data.get("documents", {})
                    self.embeddings = data.get("embeddings", {})
                    self.metadatas = data.get("metadatas", {})
                logger.info(f"Loaded {len(self.documents)} chunks from persistence")
            except Exception as e:
                logger.warning(f"Could not load persisted data: {e}")
    
    def _save(self):
        """Persist data to disk."""
        os.makedirs(self.persist_path, exist_ok=True)
        data_file = os.path.join(self.persist_path, "vector_store.pkl")
        try:
            with open(data_file, "wb") as f:
                pickle.dump({
                    "documents": self.documents,
                    "embeddings": self.embeddings,
                    "metadatas": self.metadatas
                }, f)
        except Exception as e:
            logger.error(f"Could not persist data: {e}")
    
    def add(self, ids: List[str], documents: List[str], 
            embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        """Add documents with embeddings and metadata."""
        for i, id in enumerate(ids):
            self.documents[id] = documents[i]
            self.embeddings[id] = embeddings[i]
            self.metadatas[id] = metadatas[i]
        self._save()
    
    def _matches_filter(self, metadata: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """Check if metadata matches filter conditions."""
        for key, value in where.items():
            if key not in metadata:
                return False
            
            meta_value = metadata[key]
            
            # Handle list fields (e.g., standards_referenced)
            if isinstance(meta_value, list):
                if value not in meta_value:
                    return False
            # Handle exact match
            elif meta_value != value:
                return False
        
        return True
    
    def get(self, where: Optional[Dict[str, Any]] = None, 
            include: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get documents matching filter."""
        result_ids = []
        result_documents = []
        result_metadatas = []
        
        for id, metadata in self.metadatas.items():
            if where is None or self._matches_filter(metadata, where):
                result_ids.append(id)
                if include is None or "documents" in include:
                    result_documents.append(self.documents.get(id, ""))
                if include is None or "metadatas" in include:
                    result_metadatas.append(metadata)
        
        return {
            "ids": result_ids,
            "documents": result_documents if result_documents else None,
            "metadatas": result_metadatas if result_metadatas else None
        }
    
    def query(self, query_embeddings: List[List[float]], n_results: int = 5,
              where: Optional[Dict[str, Any]] = None,
              include: Optional[List[str]] = None) -> Dict[str, Any]:
        """Query for similar documents with optional filtering."""
        if not self.embeddings:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        query_emb = np.array(query_embeddings[0])
        
        # Filter by where clause first
        candidates = []
        for id, metadata in self.metadatas.items():
            if where is None or self._matches_filter(metadata, where):
                candidates.append(id)
        
        if not candidates:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        # Calculate distances
        distances = []
        for id in candidates:
            emb = np.array(self.embeddings[id])
            # Cosine distance
            dist = 1 - np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-8)
            distances.append((id, dist))
        
        # Sort by distance
        distances.sort(key=lambda x: x[1])
        
        # Take top n_results
        top_results = distances[:n_results]
        
        result_ids = [r[0] for r in top_results]
        result_distances = [r[1] for r in top_results]
        result_documents = [self.documents.get(id, "") for id in result_ids]
        result_metadatas = [self.metadatas.get(id, {}) for id in result_ids]
        
        return {
            "ids": [result_ids],
            "documents": [result_documents],
            "metadatas": [result_metadatas],
            "distances": [result_distances]
        }
    
    def delete(self, where: Dict[str, Any]) -> int:
        """Delete documents matching filter."""
        to_delete = []
        for id, metadata in self.metadatas.items():
            if self._matches_filter(metadata, where):
                to_delete.append(id)
        
        for id in to_delete:
            del self.documents[id]
            del self.embeddings[id]
            del self.metadatas[id]
        
        self._save()
        return len(to_delete)


# Global vector store
_vector_store: Optional[SimpleVectorStore] = None


def _get_vector_store() -> SimpleVectorStore:
    """Get or create the vector store."""
    global _vector_store
    if _vector_store is None:
        settings.ensure_directories()
        _vector_store = SimpleVectorStore(settings.chroma_persist_dir)
        logger.info(f"Initialized vector store at {settings.chroma_persist_dir}")
    return _vector_store


def get_collection():
    """Get the vector store (compatibility with ChromaDB API)."""
    return _get_vector_store()


def index_chunks(chunks: List[Chunk], doc_id: str, filename: str,
                 device_name: Optional[str] = None, 
                 doc_type: str = "other") -> int:
    """Index chunks into the vector store with extended metadata."""
    if not chunks:
        return 0
    
    store = _get_vector_store()
    
    # Prepare data
    ids = []
    documents = []
    metadatas = []
    
    uploaded_at = datetime.utcnow().isoformat()
    
    for chunk in chunks:
        ids.append(chunk.metadata.chunk_id)
        documents.append(chunk.text)
        
        # Build extended metadata
        metadata = {
            "doc_id": chunk.metadata.doc_id,
            "filename": chunk.metadata.filename,
            "chunk_id": chunk.metadata.chunk_id,
            "page_number": chunk.metadata.page_number if chunk.metadata.page_number else -1,
            "chunk_index": chunk.metadata.chunk_index,
            "uploaded_at": uploaded_at,
            # Extended fields
            "device_name": device_name or chunk.metadata.device_name or "",
            "doc_type": doc_type or chunk.metadata.doc_type or "other",
            "standards_referenced": chunk.metadata.standards_referenced or [],
            "section_heading": chunk.metadata.section_heading or "",
            "requirement_ids": chunk.metadata.requirement_ids or [],
            "test_case_ids": chunk.metadata.test_case_ids or [],
            "risk_ids": chunk.metadata.risk_ids or [],
        }
        metadatas.append(metadata)
    
    # Generate embeddings
    logger.info(f"Generating embeddings for {len(documents)} chunks...")
    embeddings = get_embeddings(documents)
    
    # Add to store
    store.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    logger.info(f"Indexed {len(chunks)} chunks for document '{filename}' (doc_id={doc_id})")
    
    return len(chunks)


def get_document_chunk_count(doc_id: str) -> int:
    """Get the number of chunks for a specific document."""
    store = _get_vector_store()
    
    try:
        results = store.get(where={"doc_id": doc_id})
        return len(results["ids"]) if results and results.get("ids") else 0
    except Exception as e:
        logger.error(f"Error getting chunk count for {doc_id}: {e}")
        return 0


def list_documents() -> List[DocumentMetadata]:
    """List all indexed documents with extended metadata."""
    store = _get_vector_store()
    documents = []
    
    try:
        results = store.get(include=["metadatas"])
        
        if not results or not results.get("metadatas"):
            return documents
        
        # Group by doc_id
        doc_info: Dict[str, Dict[str, Any]] = {}
        
        for metadata in results["metadatas"]:
            doc_id = metadata.get("doc_id")
            if doc_id:
                if doc_id not in doc_info:
                    doc_info[doc_id] = {
                        "filename": metadata.get("filename", "unknown"),
                        "uploaded_at": metadata.get("uploaded_at", ""),
                        "device_name": metadata.get("device_name", ""),
                        "doc_type": metadata.get("doc_type", "other"),
                        "chunk_count": 0,
                        "standards": set()
                    }
                doc_info[doc_id]["chunk_count"] += 1
                
                # Aggregate standards
                standards = metadata.get("standards_referenced", [])
                if isinstance(standards, list):
                    doc_info[doc_id]["standards"].update(standards)
        
        # Convert to DocumentMetadata objects
        for doc_id, info in doc_info.items():
            documents.append(DocumentMetadata(
                doc_id=doc_id,
                filename=info["filename"],
                device_name=info["device_name"] if info["device_name"] else None,
                doc_type=info["doc_type"],
                chunks_indexed=info["chunk_count"],
                uploaded_at=info["uploaded_at"],
                standards_detected=sorted(list(info["standards"]))
            ))
        
        # Sort by uploaded_at descending
        documents.sort(key=lambda x: x.uploaded_at, reverse=True)
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
    
    return documents


def delete_document(doc_id: str) -> int:
    """Delete a document and all its chunks."""
    store = _get_vector_store()
    
    try:
        chunk_count = get_document_chunk_count(doc_id)
        
        if chunk_count == 0:
            return 0
        
        # Delete chunks
        store.delete(where={"doc_id": doc_id})
        
        logger.info(f"Deleted {chunk_count} chunks for document {doc_id}")
        
        return chunk_count
        
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise


def query_chunks(
    query: str,
    doc_id: Optional[str] = None,
    device_name: Optional[str] = None,
    doc_type: Optional[str] = None,
    standard: Optional[str] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Query the vector store with optional metadata filtering."""
    store = _get_vector_store()
    
    # Build filter
    where = {}
    if doc_id:
        where["doc_id"] = doc_id
    if device_name:
        where["device_name"] = device_name
    if doc_type:
        where["doc_type"] = doc_type
    # Note: standard filtering handled specially in _matches_filter
    
    # Generate query embedding
    query_embedding = get_embedding(query)
    
    # Execute query
    results = store.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where if where else None,
        include=["documents", "metadatas", "distances"]
    )
    
    # Filter by standard if specified (post-query filter for list field)
    formatted_results = []
    
    if results and results.get("ids") and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            
            # Filter by standard if specified
            if standard:
                chunk_standards = metadata.get("standards_referenced", [])
                if standard not in chunk_standards:
                    continue
            
            formatted_results.append({
                "chunk_id": chunk_id,
                "text": results["documents"][0][i] if results.get("documents") else "",
                "metadata": metadata,
                "distance": results["distances"][0][i] if results.get("distances") else 0
            })
    
    return formatted_results


def document_exists(doc_id: str) -> bool:
    """Check if a document exists."""
    return get_document_chunk_count(doc_id) > 0
