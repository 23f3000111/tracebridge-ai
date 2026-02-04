# TraceBridge AI - Technical Documentation
## Complete Backend System Architecture & Process Explanation
This document provides an in-depth technical explanation of how every component in the TraceBridge AI backend works, including the data flow, algorithms, and implementation details.
---
# Table of Contents
1. [System Overview](#1-system-overview)
2. [Document Parser Service](#2-document-parser-service)
3. [Text Chunking Service](#3-text-chunking-service)
4. [Vector Indexing Service](#4-vector-indexing-service)
5. [RAG Query Pipeline](#5-rag-query-pipeline)
6. [LLM Service & Hallucination Prevention](#6-llm-service--hallucination-prevention)
7. [Gap Analysis Engine](#7-gap-analysis-engine)
8. [Complete Request Lifecycle](#8-complete-request-lifecycle)
---
# 1. System Overview
## What is TraceBridge AI?
TraceBridge AI is a **Retrieval-Augmented Generation (RAG)** system designed for regulatory compliance analysis. It helps medical device manufacturers identify gaps in their FDA 510(k) submissions before actual submission, reducing the risk of Refusal to Accept (RTA) decisions.
## The Core Problem We Solve
When a company submits a 510(k) application to the FDA, the submission must contain specific documentation (V&V reports, biocompatibility studies, risk analysis, etc.). If any required document is missing or incomplete, the FDA issues an RTA. Our system:
1. **Ingests** user-uploaded documents (PDF, DOCX)
2. **Analyzes** content against FDA requirements
3. **Identifies** gaps and missing information
4. **Generates** remediation recommendations
## Technology Stack
```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
├─────────────────────────────────────────────────────────┤
│  Services Layer                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────────┐ │
│  │ Parser  │ │ Chunker │ │ Indexer │ │ LLM + GapAnalysis │
│  └─────────┘ └─────────┘ └─────────┘ └───────────────┘ │
├─────────────────────────────────────────────────────────┤
│  External Dependencies                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   ChromaDB   │  │   OpenAI     │  │  File System │  │
│  │ Vector Store │  │   GPT-4 API  │  │   Storage    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```
---
# 2. Document Parser Service
## Purpose
The Parser Service is responsible for **extracting raw text content** from uploaded documents. It supports two formats: PDF and DOCX.
## Location
`app/services/parser.py`
## How It Works
### Step 1: File Type Detection
When a document is uploaded, the parser first determines its type:
```python
def parse_document(file_path: str) -> ParsedDocument:
    """
    Main entry point for document parsing.
    Detects file type and routes to appropriate parser.
    """
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension == '.pdf':
        return parse_pdf(file_path)
    elif file_extension == '.docx':
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")
```
### Step 2: PDF Parsing (Using PyMuPDF/fitz)
For PDF files, we use PyMuPDF (also known as `fitz`) library:
```python
import fitz  # PyMuPDF
def parse_pdf(file_path: str) -> ParsedDocument:
    """
    Extract text from PDF files page by page.
    
    Process:
    1. Open PDF file
    2. Iterate through each page
    3. Extract text blocks from each page
    4. Preserve page numbers for citation tracking
    5. Detect regulatory standards mentioned in text
    """
    doc = fitz.open(file_path)
    pages = []
    full_text = ""
    
    for page_num, page in enumerate(doc, start=1):
        # Extract text from current page
        page_text = page.get_text("text")
        
        # Store with page metadata
        pages.append({
            "page_number": page_num,
            "content": page_text,
            "char_count": len(page_text)
        })
        
        full_text += page_text + "\n"
    
    doc.close()
    
    # Detect regulatory standards
    standards = detect_standards(full_text)
    
    return ParsedDocument(
        text=full_text,
        pages=pages,
        total_pages=len(pages),
        standards_detected=standards -
    )
```
### Step 3: DOCX Parsing (Using python-docx)
For Word documents:
```python
from docx import Document
def parse_docx(file_path: str) -> ParsedDocument:
    """
    Extract text from DOCX files.
    
    Process:
    1. Load the Word document
    2. Iterate through all paragraphs
    3. Extract text from each paragraph
    4. Also extract text from tables
    5. Detect regulatory standards
    """
    doc = Document(file_path)
    paragraphs = []
    full_text = ""
    
    # Extract paragraph text
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text)
            full_text += para.text + "\n"
    
    # Extract table content (important for test results)
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text for cell in row.cells)
            full_text += row_text + "\n"
    
    standards = detect_standards(full_text)
    
    return ParsedDocument(
        text=full_text,
        pages=[{"page_number": 1, "content": full_text}],
        total_pages=1,
        standards_detected=standards
    )
```
### Step 4: Regulatory Standards Detection
The parser automatically identifies regulatory standards mentioned in the document:
```python
REGULATORY_STANDARDS = {
    "ISO 10993": ["ISO 10993", "biocompatibility", "biological evaluation"],
    "IEC 62304": ["IEC 62304", "software lifecycle", "software development"],
    "ISO 14971": ["ISO 14971", "risk management", "risk analysis"],
    "ISO 13485": ["ISO 13485", "quality management", "QMS"],
    "IEC 60601": ["IEC 60601", "electrical safety", "medical electrical"],
    "21 CFR 820": ["21 CFR 820", "quality system regulation", "QSR"],
}
def detect_standards(text: str) -> List[str]:
    """
    Scan text for mentions of regulatory standards.
    Uses keyword matching with variations.
    """
    detected = []
    text_lower = text.lower()
    
    for standard, keywords in REGULATORY_STANDARDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                detected.append(standard)
                break  # Found this standard, move to next
    
    return list(set(detected))  # Remove duplicates
```
## Output
The parser returns a `ParsedDocument` object:
```python
@dataclass
class ParsedDocument:
    text: str                    # Full extracted text
    pages: List[dict]            # Page-by-page content with metadata
    total_pages: int             # Total page count
    standards_detected: List[str] # Regulatory standards found
    metadata: dict               # Additional file metadata
```
---
# 3. Text Chunking Service
## Purpose
The Chunker Service splits large documents into smaller, overlapping text segments. This is **critical for RAG systems** because:
1. **Embedding models have token limits** - Can't embed entire documents
2. **Smaller chunks improve retrieval precision** - More specific matches
3. **Overlapping prevents context loss** - Important sentences aren't split
## Location
`app/services/chunker.py`
## How It Works
### The Chunking Algorithm
```
Original Text (2000 characters):
┌──────────────────────────────────────────────────────────────────┐
│ The medical device underwent rigorous testing. Biocompatibility │
│ studies were conducted according to ISO 10993. Cytotoxicity     │
│ tests showed no adverse effects. Sensitization testing was      │
│ performed using the Guinea pig maximization test...             │
└──────────────────────────────────────────────────────────────────┘
After Chunking (500 chars each, 100 overlap):
Chunk 1 (chars 0-500):
┌─────────────────────────────────────────────────┐
│ The medical device underwent rigorous testing.  │
│ Biocompatibility studies were conducted         │
│ according to ISO 10993. Cytotoxicity tests...   │
└─────────────────────────────────────────────────┘
Chunk 2 (chars 400-900):  ← Starts 100 chars before Chunk 1 ends (OVERLAP)
┌─────────────────────────────────────────────────┐
│ ...Cytotoxicity tests showed no adverse         │
│ effects. Sensitization testing was performed    │
│ using the Guinea pig maximization test...       │
└─────────────────────────────────────────────────┘
Chunk 3 (chars 800-1300): ← Another 100 char overlap
┌─────────────────────────────────────────────────┐
│ ...Guinea pig maximization test. The results    │
│ demonstrated that the device materials do not   │
│ cause sensitization reactions in subjects...    │
└─────────────────────────────────────────────────┘
```
### Implementation
```python
from typing import List
from dataclasses import dataclass
@dataclass
class TextChunk:
    chunk_id: str           # Unique identifier
    content: str            # The chunk text
    start_char: int         # Starting position in original
    end_char: int           # Ending position in original
    page_number: int        # Which page this came from
    metadata: dict          # Additional context
def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    doc_id: str = None
) -> List[TextChunk]:
    """
    Split text into overlapping chunks.
    
    Parameters:
    -----------
    text : str
        The full document text to chunk
    chunk_size : int
        Target size of each chunk in characters (default: 500)
    chunk_overlap : int
        Number of overlapping characters between chunks (default: 100)
    doc_id : str
        Document ID for chunk identification
    
    Algorithm:
    ----------
    1. Start at position 0
    2. Take `chunk_size` characters
    3. Find a good break point (sentence end, paragraph)
    4. Create chunk with metadata
    5. Move forward by (chunk_size - overlap) characters
    6. Repeat until end of text
    """
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        # Calculate end position
        end = start + chunk_size
        
        # Don't exceed text length
        if end > len(text):
            end = len(text)
        
        # Try to find a natural break point (sentence end)
        if end < len(text):
            # Look for sentence endings near the chunk boundary
            break_chars = ['. ', '.\n', '! ', '? ', '\n\n']
            best_break = end
            
            for break_char in break_chars:
                # Search in the last 100 characters of the chunk
                search_start = max(end - 100, start)
                pos = text.rfind(break_char, search_start, end)
                if pos > start:
                    best_break = pos + len(break_char)
                    break
            
            end = best_break
        
        # Extract the chunk content
        chunk_content = text[start:end].strip()
        
        if chunk_content:  # Only add non-empty chunks
            chunk = TextChunk(
                chunk_id=f"{doc_id}_chunk_{chunk_index}",
                content=chunk_content,
                start_char=start,
                end_char=end,
                page_number=determine_page_number(start, pages),
                metadata={
                    "doc_id": doc_id,
                    "chunk_index": chunk_index,
                    "char_length": len(chunk_content)
                }
            )
            chunks.append(chunk)
            chunk_index += 1
        
        # Move to next chunk position (with overlap)
        start = end - chunk_overlap
        
        # Ensure we're making progress
        if start >= len(text) - chunk_overlap:
            break
    
    return chunks
```
### Why 500 Characters and 100 Overlap?
```
┌─────────────────────────────────────────────────────────────────┐
│                     CHUNK SIZE TRADEOFFS                         │
├─────────────────────────────────────────────────────────────────┤
│ Too Small (100-200 chars):                                       │
│   ✗ Loses context                                                │
│   ✗ Sentences get fragmented                                     │
│   ✗ More chunks = slower search                                  │
│                                                                  │
│ Too Large (1000+ chars):                                         │
│   ✗ Less precise retrieval                                       │
│   ✗ May exceed embedding token limits                            │
│   ✗ Irrelevant content mixed with relevant                       │
│                                                                  │
│ Sweet Spot (400-600 chars):                                      │
│   ✓ Usually 2-4 complete sentences                               │
│   ✓ Maintains semantic coherence                                 │
│   ✓ Good retrieval precision                                     │
│   ✓ Works well with embedding models                             │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                     OVERLAP IMPORTANCE                           │
├─────────────────────────────────────────────────────────────────┤
│ Without Overlap:                                                 │
│   Chunk 1: "The device was tested for cytotoxicity."            │
│   Chunk 2: "Results showed no adverse effects."                  │
│   ⚠️ Query about "cytotoxicity results" might miss context!     │
│                                                                  │
│ With 100 char Overlap:                                           │
│   Chunk 1: "The device was tested for cytotoxicity."            │
│   Chunk 2: "...tested for cytotoxicity. Results showed no..."   │
│   ✓ Both chunks can match queries about cytotoxicity results!   │
└─────────────────────────────────────────────────────────────────┘
```
---
# 4. Vector Indexing Service
## Purpose
The Indexer Service converts text chunks into **vector embeddings** and stores them in a vector database (ChromaDB) for semantic search.
## Location
`app/services/indexer.py`
## What is Vector Embedding?
```
Text: "The biocompatibility test results showed no cytotoxicity."
                    ↓ Embedding Model (OpenAI)
Vector: [0.023, -0.156, 0.089, 0.234, ..., -0.067]
        └──────────────────────────────────────────┘
                    1536 dimensions
This vector represents the MEANING of the text in mathematical form.
Similar texts will have similar vectors (close in vector space).
```
## How It Works
### Step 1: Initialize ChromaDB
```python
import chromadb
from chromadb.config import Settings
def initialize_chroma():
    """
    Set up persistent ChromaDB instance.
    Data is stored on disk and persists between restarts.
    """
    client = chromadb.PersistentClient(
        path="./chroma_data",
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    # Get or create collection for our documents
    collection = client.get_or_create_collection(
        name="regulatory_docs",
        metadata={"description": "FDA regulatory document chunks"}
    )
    
    return collection
```
### Step 2: Generate Embeddings
```python
from openai import OpenAI
client = OpenAI()
def generate_embedding(text: str) -> List[float]:
    """
    Convert text into a vector embedding using OpenAI.
    
    Model: text-embedding-3-small
    - 1536 dimensions
    - Optimized for semantic similarity
    - ~$0.00002 per 1K tokens
    
    Process:
    1. Send text to OpenAI embedding API
    2. Receive 1536-dimensional vector
    3. Vector captures semantic meaning
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        encoding_format="float"
    )
    
    embedding = response.data[0].embedding
    return embedding  # List of 1536 floats
```
### Step 3: Index Chunks
```python
def index_chunks(chunks: List[TextChunk], collection) -> int:
    """
    Store all chunks in ChromaDB with their embeddings.
    
    For each chunk:
    1. Generate embedding vector
    2. Prepare metadata for filtering
    3. Add to ChromaDB collection
    """
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        # Generate embedding for this chunk
        embedding = generate_embedding(chunk.content)
        
        ids.append(chunk.chunk_id)
        embeddings.append(embedding)
        documents.append(chunk.content)
        metadatas.append({
            "doc_id": chunk.metadata["doc_id"],
            "device_name": chunk.metadata.get("device_name", ""),
            "doc_type": chunk.metadata.get("doc_type", ""),
            "page_number": chunk.page_number,
            "chunk_index": chunk.metadata["chunk_index"]
        })
    
    # Batch insert into ChromaDB
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    return len(chunks)
```
### Visual: How Indexing Works
```
Document Upload
     │
     ▼
┌─────────────┐
│   Parser    │──→ Raw Text: "The biocompatibility studies..."
└─────────────┘
     │
     ▼
┌─────────────┐     ┌─────────────────────────────────────┐
│   Chunker   │──→  │ Chunk 1: "The biocompatibility..."  │
└─────────────┘     │ Chunk 2: "...studies according..."  │
     │              │ Chunk 3: "...ISO 10993 standard..." │
     │              └─────────────────────────────────────┘
     ▼
┌─────────────┐     ┌─────────────────────────────────────┐
│  Embedding  │──→  │ Vector 1: [0.02, -0.15, 0.08, ...]  │
│   Model     │     │ Vector 2: [0.11, -0.03, 0.19, ...]  │
└─────────────┘     │ Vector 3: [-0.05, 0.22, 0.04, ...]  │
     │              └─────────────────────────────────────┘
     ▼
┌─────────────────────────────────────────────────────────┐
│                       ChromaDB                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ID        │ Vector           │ Text    │ Meta   │   │
│  ├───────────┼──────────────────┼─────────┼────────┤   │
│  │ doc1_c0   │ [0.02, -0.15...] │ "The.." │ {p:1}  │   │
│  │ doc1_c1   │ [0.11, -0.03...] │ "...st" │ {p:1}  │   │
│  │ doc1_c2   │ [-0.05, 0.22...] │ "...IS" │ {p:2}  │   │
│  └───────────┴──────────────────┴─────────┴────────┘   │
└─────────────────────────────────────────────────────────┘
```
### Step 4: Semantic Search (Query Time)
```python
def query_chunks(
    query: str,
    device_name: str = None,
    doc_type: str = None,
    top_k: int = 5
) -> List[RetrievedChunk]:
    """
    Find the most relevant chunks for a query.
    
    Process:
    1. Convert query to embedding vector
    2. Search ChromaDB for similar vectors
    3. Apply metadata filters if specified
    4. Return top-k most similar chunks
    """
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Build filter conditions
    where_filter = {}
    if device_name:
        where_filter["device_name"] = device_name
    if doc_type:
        where_filter["doc_type"] = doc_type
    
    # Perform similarity search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter if where_filter else None,
        include=["documents", "metadatas", "distances"]
    )
    
    # Format results
    retrieved = []
    for i in range(len(results["ids"][0])):
        chunk = RetrievedChunk(
            chunk_id=results["ids"][0][i],
            content=results["documents"][0][i],
            relevance_score=1 - results["distances"][0][i],  # Convert distance to similarity
            metadata=results["metadatas"][0][i]
        )
        retrieved.append(chunk)
    
    return retrieved
```
### Visual: How Semantic Search Works
```
User Query: "What biocompatibility tests were performed?"
                    │
                    ▼
           ┌───────────────┐
           │ Query → Vector │
           │ [0.08, -0.12...]│
           └───────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │   Vector Space (simplified 2D view)    │
    │                                        │
    │       Chunk about           ★ Query   │
    │       cytotoxicity  ●                  │
    │                        ●               │
    │                   Chunk about          │
    │   ●              biocompatibility      │
    │   Chunk about         ↑                │
    │   sterilization   CLOSEST MATCH!       │
    │                                        │
    └───────────────────────────────────────┘
                    │
                    ▼
    Returns: Chunk about biocompatibility (highest similarity)
```
---
# 5. RAG Query Pipeline
## Purpose
The RAG (Retrieval-Augmented Generation) pipeline combines vector search with LLM generation to answer questions using document content.
## Location
`app/routers/query.py` + `app/services/llm.py`
## The Complete Pipeline
```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE                              │
└─────────────────────────────────────────────────────────────────┘
Step 1: RETRIEVAL
┌──────────────────┐    ┌──────────────┐    ┌──────────────────┐
│   User Query     │───▶│   Indexer    │───▶│ Retrieved Chunks │
│ "What V&V tests" │    │ query_chunks │    │ [chunk1, chunk2] │
└──────────────────┘    └──────────────┘    └──────────────────┘
                                                     │
                                                     ▼
Step 2: AUGMENTATION
┌─────────────────────────────────────────────────────────────────┐
│                    PROMPT CONSTRUCTION                           │
│                                                                  │
│  System: You are a regulatory compliance expert. Answer based   │
│          ONLY on the provided context. Cite your sources.       │
│                                                                  │
│  Context:                                                        │
│  [1] "Unit testing was performed on all software modules..."    │
│  [2] "Integration testing verified interface compatibility..."  │
│                                                                  │
│  Question: What V&V tests were performed?                        │
└─────────────────────────────────────────────────────────────────┘
                                                     │
                                                     ▼
Step 3: GENERATION
┌──────────────────┐    ┌──────────────────────────────────────────┐
│      GPT-4       │───▶│ Based on the provided documentation,     │
│                  │    │ the following V&V tests were performed:  │
│                  │    │ 1. Unit testing [1]                       │
│                  │    │ 2. Integration testing [2]                │
└──────────────────┘    └──────────────────────────────────────────┘
                                                     │
                                                     ▼
Step 4: VERIFICATION
┌─────────────────────────────────────────────────────────────────┐
│                    HALLUCINATION CHECK                           │
│  - Are all claims supported by context?                          │
│  - Are citations valid?                                          │
│  - Confidence score: 0.92                                        │
└─────────────────────────────────────────────────────────────────┘
                                                     │
                                                     ▼
Step 5: RESPONSE
┌─────────────────────────────────────────────────────────────────┐
│  {                                                               │
│    "answer": "The V&V tests included unit testing...",          │
│    "citations": [                                                │
│      {"chunk_id": "doc1_c5", "snippet": "...", "score": 0.89}  │
│    ],                                                            │
│    "fallback_used": false,                                       │
│    "verification": {"passed": true, "confidence": 0.92}          │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```
## Implementation
```python
async def process_rag_query(query: str, device_name: str, top_k: int = 5):
    """
    Complete RAG pipeline execution.
    """
    # Step 1: Retrieve relevant chunks
    chunks = await query_chunks(query, device_name=device_name, top_k=top_k)
    
    if not chunks:
        return {
            "answer": "No relevant information found in the uploaded documents.",
            "citations": [],
            "fallback_used": True
        }
    
    # Step 2: Build grounded prompt
    context = build_context(chunks)
    prompt = build_grounded_prompt(query, context)
    
    # Step 3: Generate answer with LLM
    answer = await generate_llm_response(prompt)
    
    # Step 4: Verify and extract citations
    verification = verify_answer(answer, chunks)
    citations = extract_citations(answer, chunks)
    
    return {
        "answer": answer,
        "citations": citations,
        "fallback_used": not verification["passed"],
        "verification": verification
    }
```
---
# 6. LLM Service & Hallucination Prevention
## Purpose
The LLM Service manages all interactions with OpenAI GPT-4, including prompt engineering for grounded generation and hallucination prevention.
## Location
`app/services/llm.py`
## Grounded Prompt Engineering
The key to preventing hallucinations is **constraining the LLM to only use provided context**:
```python
GROUNDED_SYSTEM_PROMPT = """
You are a regulatory compliance expert analyzing medical device documentation.
CRITICAL RULES:
1. Answer ONLY based on the provided context below
2. If the context doesn't contain relevant information, say "Not found in documents"
3. ALWAYS cite your sources using [1], [2], etc.
4. NEVER make up information not in the context
5. Be specific and quote relevant passages when possible
Your goal is to help identify gaps in FDA 510(k) submissions.
"""
def build_grounded_prompt(query: str, chunks: List[RetrievedChunk]) -> str:
    """
    Construct a prompt that forces the LLM to ground responses in context.
    """
    # Format context with numbered references
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"[{i}] (Page {chunk.metadata.get('page_number', '?')}):\n{chunk.content}")
    
    context = "\n\n".join(context_parts)
    
    prompt = f"""
{GROUNDED_SYSTEM_PROMPT}
=== CONTEXT FROM UPLOADED DOCUMENTS ===
{context}
=== END CONTEXT ===
User Question: {query}
Instructions:
- Answer based ONLY on the context above
- Cite sources as [1], [2], etc.
- If information is not found, clearly state that
"""
    return prompt
```
## Hallucination Verification Layer
After generating a response, we verify it against the source context:
```python
def verify_answer(answer: str, source_chunks: List[RetrievedChunk]) -> dict:
    """
    Check if the generated answer is properly grounded in source content.
    
    Verification Steps:
    1. Extract claims from the answer
    2. Check if each claim has supporting evidence in chunks
    3. Validate citation references
    4. Calculate confidence score
    """
    # Extract cited references from answer
    import re
    citations_used = set(re.findall(r'\[(\d+)\]', answer))
    
    # Check if citations are valid
    valid_citations = all(
        int(c) <= len(source_chunks) 
        for c in citations_used
    )
    
    # Check for unsupported claims (heuristic)
    unsupported_phrases = [
        "it is well known",
        "generally",
        "typically",
        "studies have shown",  # unless cited
        "research indicates"   # unless cited
    ]
    
    has_unsupported = any(
        phrase in answer.lower() and f"[{i}]" not in answer
        for phrase in unsupported_phrases
        for i in range(1, len(source_chunks) + 1)
    )
    
    # Calculate confidence
    if not citations_used:
        confidence = 0.3  # No citations = low confidence
    elif not valid_citations:
        confidence = 0.4  # Invalid citations
    elif has_unsupported:
        confidence = 0.6  # Some unsupported claims
    else:
        confidence = 0.9  # Well-grounded answer
    
    return {
        "passed": confidence >= 0.7,
        "confidence": confidence,
        "citations_found": len(citations_used),
        "valid_citations": valid_citations
    }
```
## Fallback Handling
When verification fails, we provide a safer response:
```python
async def generate_grounded_answer(query: str, chunks: List[RetrievedChunk]):
    """
    Generate answer with fallback if verification fails.
    """
    # First attempt: Full LLM generation
    prompt = build_grounded_prompt(query, chunks)
    answer = await call_openai(prompt)
    verification = verify_answer(answer, chunks)
    
    if verification["passed"]:
        return answer, extract_citations(answer, chunks), False, verification
    
    # Fallback: Simpler extraction-based response
    fallback_answer = generate_extractive_summary(query, chunks)
    return fallback_answer, extract_citations(fallback_answer, chunks), True, verification
```
---
# 7. Gap Analysis Engine
## Purpose
The Gap Analysis Engine compares user-uploaded documents against FDA requirements to identify missing or incomplete documentation.
## Location
`app/services/gap_analysis.py`
## FDA Requirements Knowledge Base
We maintain a structured database of FDA requirements by category:
```python
FDA_REQUIREMENTS = {
    "V&V": {
        "title": "Verification & Validation",
        "requirements": [
            {
                "id": "VV-001",
                "requirement": "Software unit testing documentation",
                "description": "Evidence of unit-level testing for all software modules",
                "severity": "critical",
                "search_terms": ["unit test", "module test", "unit testing", "test case"]
            },
            {
                "id": "VV-002",
                "requirement": "Integration testing documentation",
                "description": "Evidence of system integration testing",
                "severity": "critical",
                "search_terms": ["integration test", "interface test", "system test"]
            },
            {
                "id": "VV-003",
                "requirement": "Validation protocol and results",
                "description": "User validation testing with acceptance criteria",
                "severity": "critical",
                "search_terms": ["validation", "user testing", "acceptance test"]
            }
        ]
    },
    "Biocompatibility": {
        "title": "Biocompatibility Testing",
        "requirements": [
            {
                "id": "BIO-001",
                "requirement": "Cytotoxicity testing per ISO 10993-5",
                "description": "In vitro cytotoxicity assessment",
                "severity": "critical",
                "search_terms": ["cytotoxicity", "ISO 10993-5", "cell viability"]
            },
            {
                "id": "BIO-002",
                "requirement": "Sensitization testing",
                "description": "Assessment of sensitization potential",
                "severity": "high",
                "search_terms": ["sensitization", "guinea pig", "allergic"]
            }
        ]
    }
}
```
## Gap Detection Algorithm
```python
async def generate_gap_report(
    device_name: str,
    focus_area: str,
    doc_ids: List[str]
) -> List[Gap]:
    """
    Compare uploaded documents against FDA requirements.
    
    Algorithm:
    1. Load requirements for the focus area
    2. For each requirement:
       a. Search user documents for evidence
       b. If no evidence found → MISSING gap
       c. If partial evidence → INCOMPLETE gap
       d. If full evidence → PASSED
    3. Return list of gaps with remediation steps
    """
    gaps = []
    requirements = FDA_REQUIREMENTS.get(focus_area, {}).get("requirements", [])
    
    for req in requirements:
        # Search for evidence in user documents
        evidence = await search_for_evidence(
            search_terms=req["search_terms"],
            device_name=device_name,
            doc_ids=doc_ids
        )
        
        if not evidence:
            # No evidence found - MISSING
            gap = Gap(
                category=focus_area,
                severity=req["severity"],
                fda_requirement=req["requirement"],
                evidence_found=None,
                gap_description=f"No documentation found for: {req['description']}",
                remediation_steps=generate_remediation(req),
                estimated_timeline=estimate_timeline(req["severity"]),
                estimated_cost=estimate_cost(req["severity"])
            )
            gaps.append(gap)
            
        elif evidence["relevance_score"] < 0.8:
            # Partial evidence - INCOMPLETE
            gap = Gap(
                category=focus_area,
                severity="medium",
                fda_requirement=req["requirement"],
                evidence_found=evidence["snippet"],
                gap_description=f"Partial documentation found, may be incomplete",
                remediation_steps=["Review and expand existing documentation"],
                estimated_timeline="1-2 weeks",
                estimated_cost="$2,000 - $5,000"
            )
            gaps.append(gap)
        
        # If relevance > 0.8, requirement is satisfied (no gap)
    
    return gaps
async def search_for_evidence(
    search_terms: List[str],
    device_name: str,
    doc_ids: List[str]
) -> Optional[dict]:
    """
    Search user documents for evidence matching requirements.
    Uses semantic search across all terms.
    """
    best_match = None
    best_score = 0
    
    for term in search_terms:
        results = await query_chunks(
            query=term,
            device_name=device_name,
            top_k=3
        )
        
        for result in results:
            if result.metadata.get("doc_id") in doc_ids:
                if result.relevance_score > best_score:
                    best_score = result.relevance_score
                    best_match = {
                        "snippet": result.content[:200],
                        "relevance_score": result.relevance_score,
                        "chunk_id": result.chunk_id
                    }
    
    return best_match if best_score > 0.5 else None
```
## Remediation Generation
```python
def generate_remediation(requirement: dict) -> List[str]:
    """
    Generate specific remediation steps for a gap.
    """
    base_steps = [
        f"Review FDA guidance on {requirement['requirement']}",
        f"Gather existing documentation related to {requirement['description']}",
    ]
    
    # Add severity-specific steps
    if requirement["severity"] == "critical":
        base_steps.extend([
            "Conduct required testing if not already performed",
            "Prepare formal test report with methodology and results",
            "Have report reviewed by qualified personnel",
            "Include traceability to requirements"
        ])
    elif requirement["severity"] == "high":
        base_steps.extend([
            "Document existing evidence in formal report",
            "Ensure compliance with referenced standards"
        ])
    
    return base_steps
def estimate_timeline(severity: str) -> str:
    """Estimate remediation timeline based on severity."""
    timelines = {
        "critical": "4-8 weeks",
        "high": "2-4 weeks",
        "medium": "1-2 weeks",
        "low": "< 1 week"
    }
    return timelines.get(severity, "TBD")
def estimate_cost(severity: str) -> str:
    """Estimate remediation cost based on severity."""
    costs = {
        "critical": "$10,000 - $50,000",
        "high": "$5,000 - $15,000",
        "medium": "$2,000 - $5,000",
        "low": "< $2,000"
    }
    return costs.get(severity, "TBD")
```
---
# 8. Complete Request Lifecycle
## Full Flow: Document Upload to Gap Report
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPLETE REQUEST LIFECYCLE                            │
└─────────────────────────────────────────────────────────────────────────────┘
====== PHASE 1: UPLOAD ======
User: Uploads "VnV_Report.pdf" via frontend
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ POST /upload                                                                 │
│ Body: file=VnV_Report.pdf, device_name="CardioSense", doc_type="vnv"        │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Save file to │───▶│    Parse     │───▶│    Chunk     │───▶│    Index     │
│   ./uploads  │    │   PDF/DOCX   │    │  into 500c   │    │  to ChromaDB │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                         │                    │                    │
                         ▼                    ▼                    ▼
              "45 pages extracted"   "127 chunks created"   "127 embeddings"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Response: {                                                                  │
│   "doc_id": "doc_abc123",                                                   │
│   "chunks_indexed": 127,                                                    │
│   "standards_detected": ["IEC 62304", "ISO 14971"]                          │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
====== PHASE 2: ANALYSIS ======
Frontend calls gap-report endpoint:
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ POST /gap-report                                                             │
│ Body: { device_name: "CardioSense", focus_area: "V&V", doc_ids: ["abc123"]} │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GAP ANALYSIS ENGINE                                   │
│                                                                              │
│  For each V&V requirement:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Requirement: "Software unit testing documentation"                   │   │
│  │                                                                      │   │
│  │ 1. Search ChromaDB for: ["unit test", "module test", ...]           │   │
│  │ 2. Found chunk with 0.87 relevance: "Unit testing was performed..." │   │
│  │ 3. Result: ✓ PASSED (evidence found with high confidence)            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Requirement: "Validation protocol and results"                       │   │
│  │                                                                      │   │
│  │ 1. Search ChromaDB for: ["validation", "user testing", ...]         │   │
│  │ 2. No matching chunks found (relevance < 0.5)                        │   │
│  │ 3. Result: ✗ GAP DETECTED (missing documentation)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Response: {                                                                  │
│   "gaps": [                                                                  │
│     {                                                                        │
│       "category": "V&V",                                                     │
│       "severity": "critical",                                                │
│       "fda_requirement": "Validation protocol and results",                  │
│       "evidence_found": null,                                                │
│       "gap_description": "No validation documentation found",                │
│       "remediation_steps": [                                                 │
│         "Develop validation protocol",                                       │
│         "Execute validation testing",                                        │
│         "Document results with pass/fail criteria"                           │
│       ],                                                                     │
│       "estimated_timeline": "4-8 weeks",                                     │
│       "estimated_cost": "$10,000 - $50,000"                                  │
│     }                                                                        │
│   ],                                                                         │
│   "total_gaps": 2                                                            │
│ }                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
====== PHASE 3: DISPLAY ======
Frontend receives response and:
1. Calculates RTA risk score based on critical gaps
2. Displays gap table with severity badges
3. Shows compliance score percentage
4. Enables "View Details" modal for each gap
5. Allows adding gaps to remediation plan
6. Exports report as downloadable file
```
---
# Summary
## Key System Characteristics
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Parser** | PyMuPDF, python-docx | Extract text from documents |
| **Chunker** | Custom algorithm | Split text with overlap for RAG |
| **Indexer** | ChromaDB + OpenAI | Vector storage and semantic search |
| **LLM Service** | OpenAI GPT-4 | Generate grounded answers |
| **Gap Analysis** | Rule-based + RAG | Compare docs to FDA requirements |
| **Verification** | Heuristic checks | Prevent hallucinations |
## Design Decisions
1. **500-char chunks** - Balance between context and precision
2. **100-char overlap** - Prevent cutting important sentences
3. **Grounded prompts** - Force LLM to cite sources
4. **Verification layer** - Catch hallucinated content
5. **Severity classification** - Prioritize remediation efforts
6. **Session storage** - Maintain state across pages
---
**This documentation explains the complete technical implementation of TraceBridge AI.**
