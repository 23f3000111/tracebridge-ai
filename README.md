# TraceBridge AI - PoC Backend (Milestone 1)

A lightweight RAG-based SaaS backend for FDA 510(k) documentation gap detection.

## Overview

TraceBridge AI helps medical device companies detect documentation gaps before FDA 510(k) submission. This PoC validates the core RAG pipeline:

- **Multi-document upload** (PDF/DOCX)
- **Text extraction** with page-level metadata
- **Intelligent chunking** with overlap
- **Vector indexing** using in-memory store with persistence
- **Semantic search** ready for RAG queries (Milestone 2)

## Project Structure

```
TraceBridge/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── documents.py     # Upload/list/delete endpoints
│   └── services/
│       ├── __init__.py
│       ├── parser.py        # PDF/DOCX parsing
│       ├── chunker.py       # Text chunking
│       ├── embeddings.py    # Embedding generation
│       └── vector_store.py  # Vector store operations
├── data/
│   └── uploads/             # Uploaded documents
├── chroma_db/               # Vector database storage
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- pip

### 2. Setup Environment

```bash
# Navigate to project directory
cd TraceBridge

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# If no OpenAI key is provided, local embeddings will be used
```

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | None (uses local) |
| `EMBEDDING_MODEL` | OpenAI embedding model name | `text-embedding-3-small` |
| `CHROMA_PERSIST_DIR` | Vector store path | `./chroma_db` |
| `UPLOAD_DIR` | Uploaded files storage | `./data/uploads` |
| `CHUNK_SIZE` | Maximum chunk size (chars) | `500` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |

### 4. Run the Server

```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "embedding_mode": "local"
}
```

### Upload Document

Upload a PDF or DOCX file for indexing.

```bash
# Using curl (Linux/macOS)
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your-document.pdf"

# Using PowerShell (Windows)
$filePath = "C:\path\to\your-document.docx"
$uri = "http://localhost:8000/upload"
$boundary = [System.Guid]::NewGuid().ToString()
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileContent = [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileBytes)
$body = "--$boundary`r`nContent-Disposition: form-data; name=`"file`"; filename=`"document.docx`"`r`nContent-Type: application/octet-stream`r`n`r`n$fileContent`r`n--$boundary--`r`n"
Invoke-RestMethod -Uri $uri -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $body
```

Response:
```json
{
  "success": true,
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "your-document.pdf",
  "chunks_indexed": 42
}
```

### List Documents

Get all uploaded documents.

```bash
# Using curl
curl http://localhost:8000/documents

# Using PowerShell
Invoke-RestMethod -Uri http://localhost:8000/documents -Method Get
```

Response:
```json
{
  "documents": [
    {
      "doc_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "your-document.pdf",
      "chunks_indexed": 42,
      "uploaded_at": "2025-01-31T12:00:00.000000"
    }
  ],
  "total_count": 1
}
```

### Delete Document

Delete a document and its indexed chunks.

```bash
# Using curl
curl -X DELETE "http://localhost:8000/documents/{doc_id}"

# Using PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/documents/{doc_id}" -Method Delete
```

Response:
```json
{
  "success": true,
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Document deleted successfully",
  "chunks_deleted": 42
}
```

## Embedding Options

### OpenAI Embeddings (Recommended for production)

Set your OpenAI API key in `.env`:
```
OPENAI_API_KEY=sk-your-api-key-here
EMBEDDING_MODEL=text-embedding-3-small
```

### Local Embeddings (Default, no API key needed)

If no valid OpenAI key is provided, the system automatically uses `sentence-transformers` with the `all-MiniLM-L6-v2` model.

**Note**: First run with local embeddings will download the model (~100MB).

## Vector Store

This PoC uses a simple in-memory vector store with disk persistence (numpy + pickle) for Python 3.14 compatibility. The store:

- Uses cosine similarity for semantic search
- Persists data to `./chroma_db/vector_store.pkl`
- Supports filtering by document ID
- Handles all standard CRUD operations

For production use, consider migrating to:
- **ChromaDB** (when Python 3.14 binaries are available)
- **Pinecone** (managed vector database)
- **Weaviate** (open-source vector database)

## Development

### Running Tests

```bash
# (Tests will be added in Milestone 2)
pytest tests/
```

### Code Structure

- **config.py**: Environment configuration with validation
- **models.py**: Pydantic models for API request/response
- **parser.py**: PyMuPDF for PDFs, python-docx for Word files
- **chunker.py**: Character-based chunking with smart boundary detection
- **embeddings.py**: Dual support for OpenAI and local embeddings
- **vector_store.py**: Simple vector store with numpy cosine similarity

## Milestone Status

### ✅ Milestone 1 (Complete)
- [x] FastAPI scaffold
- [x] Multi-document upload (PDF/DOCX)
- [x] Text parsing with page metadata
- [x] Chunking with overlap
- [x] Vector indexing
- [x] GET /documents endpoint
- [x] DELETE /documents/{doc_id} endpoint

### 🔜 Milestone 2 (Upcoming)
- [ ] RAG /query endpoint with citations
- [ ] LLM integration (OpenAI)
- [ ] Hallucination mitigation
- [ ] Gap report generation
- [ ] Dockerfile
- [ ] Deployment instructions

## License

This is a Proof of Concept project for TraceBridge AI.
