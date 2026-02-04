"""
TraceBridge AI - Embeddings Service
Handles embedding generation using OpenAI or local sentence-transformers.
"""

from typing import List, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Global embedding model instance (lazy loaded)
_local_model = None
_openai_client = None


def _get_local_model():
    """Lazy load the local sentence-transformers model."""
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading local embedding model: all-MiniLM-L6-v2")
        _local_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _local_model


def _get_openai_client():
    """Lazy load the OpenAI client."""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def get_embeddings_openai(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using OpenAI API.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    client = _get_openai_client()
    
    # OpenAI has a limit on batch size, process in batches
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=batch
        )
        
        # Extract embeddings in order
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
    
    logger.info(f"Generated {len(all_embeddings)} embeddings using OpenAI ({settings.embedding_model})")
    return all_embeddings


def get_embeddings_local(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using local sentence-transformers model.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    model = _get_local_model()
    
    # Generate embeddings
    embeddings = model.encode(texts, convert_to_numpy=True)
    
    # Convert to list of lists
    embeddings_list = embeddings.tolist()
    
    logger.info(f"Generated {len(embeddings_list)} embeddings using local model")
    return embeddings_list


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using the configured method (OpenAI or local).
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    if settings.use_openai_embeddings:
        logger.info("Using OpenAI embeddings")
        return get_embeddings_openai(texts)
    else:
        logger.info("Using local embeddings (sentence-transformers)")
        return get_embeddings_local(texts)


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector
    """
    embeddings = get_embeddings([text])
    return embeddings[0] if embeddings else []
