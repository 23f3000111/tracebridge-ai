"""
TraceBridge AI - LLM Service
OpenAI integration with grounded answering and hallucination mitigation.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI

from app.config import settings
from app.models import Citation, VerificationResult

logger = logging.getLogger(__name__)

# Global OpenAI client (lazy loaded)
_openai_client = None


def _get_openai_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _openai_client
    if _openai_client is None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


# System prompts
GROUNDED_ANSWER_SYSTEM_PROMPT = """You are TraceBridge AI, a regulatory compliance assistant for FDA 510(k) medical device submissions.

CRITICAL RULES:
1. ONLY answer based on the provided source documents. Do NOT use any external knowledge.
2. If the sources do not contain enough information to answer the question, say: "Not enough evidence found in the uploaded documents to answer this question."
3. Always cite your sources using [Source X] format where X is the source number.
4. Be precise and factual. Do not speculate or make assumptions.
5. If asked about specific requirements, tests, or standards, only mention them if they appear in the sources.

When answering:
- Start with a direct answer if the sources support one
- Quote relevant passages when helpful
- Acknowledge limitations in the available evidence
- Never fabricate test results, requirement IDs, or compliance claims
"""

EVIDENCE_CHECK_SYSTEM_PROMPT = """You are a verification assistant. Your job is to check if an answer is properly grounded in the provided sources.

Analyze the answer and sources, then respond with a JSON object:
{
  "source_grounded": true/false,  // Is every claim in the answer supported by sources?
  "evidence_confirmed": true/false,  // Are specific requirements/tests mentioned actually in sources?
  "needs_human_review": true/false,  // Should this be reviewed by a human?
  "confidence_score": 0.0-1.0,  // How confident are you in the answer's accuracy?
  "issues": []  // List any specific issues found
}

Be strict. If you find any claim not directly supported by sources, mark source_grounded as false.
"""


def format_sources_for_prompt(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks as sources for the LLM prompt."""
    if not chunks:
        return "No sources available."
    
    sources = []
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        page = metadata.get("page_number", "N/A")
        filename = metadata.get("filename", "Unknown")
        
        source_header = f"[Source {i}] (File: {filename}, Page: {page})"
        source_text = chunk.get("text", "")
        
        sources.append(f"{source_header}\n{source_text}")
    
    return "\n\n---\n\n".join(sources)


def generate_grounded_answer(
    query: str,
    chunks: List[Dict[str, Any]],
    model: str = None
) -> Tuple[str, bool]:
    """
    Generate a grounded answer using retrieved chunks.
    
    Args:
        query: User question
        chunks: Retrieved chunks with text and metadata
        model: Optional model override
        
    Returns:
        Tuple of (answer, fallback_used)
    """
    if not chunks:
        return (
            "Not enough evidence found in the uploaded documents to answer this question.",
            True
        )
    
    model = model or settings.llm_model
    
    # Check if OpenAI is available
    if not settings.use_openai_embeddings:
        # Fallback for no API key - return a simple extractive answer
        return _generate_fallback_answer(query, chunks)
    
    try:
        client = _get_openai_client()
        
        # Format sources
        sources_text = format_sources_for_prompt(chunks)
        
        # Build user message
        user_message = f"""Question: {query}

Sources:
{sources_text}

Please answer the question based ONLY on the sources above. Cite sources using [Source X] format."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": GROUNDED_ANSWER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,  # Low temperature for factual responses
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Check if the model returned a fallback
        fallback_phrases = [
            "not enough evidence",
            "cannot find",
            "no information",
            "sources do not contain",
            "unable to find",
            "not mentioned in"
        ]
        
        fallback_used = any(phrase in answer.lower() for phrase in fallback_phrases)
        
        return answer, fallback_used
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return _generate_fallback_answer(query, chunks)


def _generate_fallback_answer(
    query: str,
    chunks: List[Dict[str, Any]]
) -> Tuple[str, bool]:
    """Generate a simple extractive answer without LLM."""
    if not chunks:
        return (
            "Not enough evidence found in the uploaded documents to answer this question.",
            True
        )
    
    # Build a simple answer from top chunks
    answer_parts = ["Based on the uploaded documents:\n"]
    
    for i, chunk in enumerate(chunks[:3], 1):
        metadata = chunk.get("metadata", {})
        page = metadata.get("page_number", "N/A")
        text = chunk.get("text", "")[:300]
        
        answer_parts.append(f"\n[Source {i}] (Page {page}):\n\"{text}...\"")
    
    answer_parts.append("\n\nNote: This is an extractive summary. Enable OpenAI API for full RAG capabilities.")
    
    return "\n".join(answer_parts), False


def verify_answer(
    answer: str,
    chunks: List[Dict[str, Any]],
    model: str = None
) -> VerificationResult:
    """
    Verify that an answer is properly grounded in sources.
    
    Args:
        answer: The generated answer
        chunks: The source chunks used
        model: Optional model override
        
    Returns:
        VerificationResult with grounding status
    """
    # Quick check - if no real answer, it's grounded (fallback)
    if "not enough evidence" in answer.lower():
        return VerificationResult(
            source_grounded=True,
            evidence_confirmed=True,
            needs_human_review=False,
            confidence_score=1.0
        )
    
    if not settings.use_openai_embeddings:
        # Without LLM, assume grounded but suggest human review
        return VerificationResult(
            source_grounded=True,
            evidence_confirmed=True,
            needs_human_review=True,
            confidence_score=0.7
        )
    
    try:
        client = _get_openai_client()
        model = model or settings.llm_model
        
        sources_text = format_sources_for_prompt(chunks)
        
        user_message = f"""Answer to verify:
{answer}

Sources used:
{sources_text}

Verify if the answer is properly grounded in the sources."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": EVIDENCE_CHECK_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        import json
        try:
            # Try to extract JSON from response
            if "{" in result_text:
                json_start = result_text.index("{")
                json_end = result_text.rindex("}") + 1
                result_json = json.loads(result_text[json_start:json_end])
                
                return VerificationResult(
                    source_grounded=result_json.get("source_grounded", True),
                    evidence_confirmed=result_json.get("evidence_confirmed", True),
                    needs_human_review=result_json.get("needs_human_review", False),
                    confidence_score=result_json.get("confidence_score", 0.8)
                )
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Default if parsing fails
        return VerificationResult(
            source_grounded=True,
            evidence_confirmed=True,
            needs_human_review=True,
            confidence_score=0.7
        )
        
    except Exception as e:
        logger.error(f"Error verifying answer: {e}")
        return VerificationResult(
            source_grounded=True,
            evidence_confirmed=True,
            needs_human_review=True,
            confidence_score=0.5
        )


def extract_citations(
    chunks: List[Dict[str, Any]],
    max_snippet_length: int = 150
) -> List[Citation]:
    """
    Extract citations from retrieved chunks.
    
    Args:
        chunks: Retrieved chunks
        max_snippet_length: Maximum length of snippet
        
    Returns:
        List of Citation objects
    """
    citations = []
    
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        text = chunk.get("text", "")
        distance = chunk.get("distance", 0)
        
        # Create snippet
        snippet = text[:max_snippet_length]
        if len(text) > max_snippet_length:
            snippet += "..."
        
        # Convert distance to relevance score (1 - distance for cosine)
        relevance = max(0, min(1, 1 - distance))
        
        citations.append(Citation(
            chunk_id=metadata.get("chunk_id", "unknown"),
            page_number=metadata.get("page_number") if metadata.get("page_number", -1) > 0 else None,
            snippet=snippet,
            relevance_score=round(relevance, 3)
        ))
    
    return citations
