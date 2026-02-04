# TraceBridge AI

**AI-Powered FDA 510(k) Regulatory Compliance Analysis Platform**

TraceBridge AI uses Retrieval-Augmented Generation (RAG) to analyze medical device submissions against FDA requirements, automatically detecting documentation gaps and predicting Refusal to Accept (RTA) risk.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Landing  │→ │  Upload  │→ │ Analysis │→ │ Results  │→ │ Remediation  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ HTTP/REST
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI + Python)                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         API LAYER (Routers)                          │    │
│  │  POST /upload    POST /query    POST /gap-report    GET /documents   │    │
│  └─────────────────────────────────┬───────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────┴───────────────────────────────────┐    │
│  │                        SERVICE LAYER                                 │    │
│  │  ┌──────────┐  ┌───────────┐  ┌─────────────┐  ┌────────────────┐  │    │
│  │  │  Parser  │  │  Chunker  │  │   Indexer   │  │  LLM Service   │  │    │
│  │  │ PDF/DOCX │  │ 500 chars │  │ Embeddings  │  │ GPT-4 + Guard  │  │    │
│  │  └──────────┘  └───────────┘  └─────────────┘  └────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────────────────────┐  │    │
│  │  │                    Gap Analysis Service                       │  │    │
│  │  │    FDA Requirements Matching + Severity Classification        │  │    │
│  │  └──────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
           ┌──────────────┐            ┌──────────────┐
           │   ChromaDB   │            │   OpenAI     │
           │ Vector Store │            │   GPT-4 API  │
           │ (Embeddings) │            │  (text-gen)  │
           └──────────────┘            └──────────────┘
```

---

## 📁 Project Structure

```
TraceBridge/
├── app/                        # Backend API
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Environment settings
│   ├── models.py               # Pydantic schemas
│   ├── routers/
│   │   ├── documents.py        # /upload, /documents endpoints
│   │   └── query.py            # /query, /gap-report endpoints
│   └── services/
│       ├── parser.py           # PDF/DOCX parsing
│       ├── chunker.py          # Text chunking with overlap
│       ├── indexer.py          # ChromaDB vector indexing
│       ├── llm.py              # OpenAI integration + verification
│       └── gap_analysis.py     # FDA requirement matching
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── App.jsx             # Router setup
│   │   ├── index.css           # Design system
│   │   ├── api/client.js       # Backend API client
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── StepIndicator.jsx
│   │   │   ├── GapDetailModal.jsx
│   │   │   └── RemediationPlanModal.jsx
│   │   └── pages/
│   │       ├── Landing.jsx
│   │       ├── Upload.jsx
│   │       ├── Analysis.jsx
│   │       ├── Results.jsx
│   │       └── Documentation.jsx
│   └── package.json
│
├── uploads/                    # Stored uploaded files
├── chroma_data/               # Vector database storage
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── docker-compose.yml         # Container deployment
```

---

## 🔄 Data Flow

### 1. Document Upload Flow
```
User uploads PDF/DOCX
        ↓
[Parser] Extract text from document
        ↓
[Chunker] Split into 500-char chunks (100 overlap)
        ↓
[Indexer] Generate embeddings via OpenAI
        ↓
[ChromaDB] Store vectors with metadata
        ↓
Return: doc_id, chunks_indexed, standards_detected
```

### 2. RAG Query Flow
```
User query: "What V&V activities are documented?"
        ↓
[Indexer] Semantic search in ChromaDB
        ↓
Retrieve top-k relevant chunks
        ↓
[LLM Service] Build grounded prompt with context
        ↓
[GPT-4] Generate answer citing sources
        ↓
[Verification] Check for hallucination
        ↓
Return: answer, citations[], fallback_used, verification
```

### 3. Gap Analysis Flow
```
Request: device_name="CardioSense", focus_area="V&V"
        ↓
[Gap Service] Load FDA requirements for focus area
        ↓
[Indexer] Search user docs for each requirement
        ↓
[LLM] Compare and identify gaps
        ↓
Classify severity: critical | high | medium | low
        ↓
Generate remediation steps
        ↓
Return: gaps[], total_gaps, severity_breakdown
```

---

## 🧠 RAG Implementation Details

### Embedding Strategy
- **Model**: OpenAI `text-embedding-3-small`
- **Dimension**: 1536
- **Fallback**: Sentence Transformers (offline)

### Chunking Strategy
```python
chunk_size = 500      # Characters per chunk
chunk_overlap = 100   # Overlap between chunks
```

### Retrieval Parameters
```python
top_k = 5             # Default chunks to retrieve
similarity_threshold = 0.7  # Minimum relevance
```

### Hallucination Mitigation
1. **Grounded Prompts**: LLM instructed to cite only provided context
2. **Verification Layer**: Post-generation confidence check
3. **Fallback Handling**: Falls back to retrieval-only if verification fails
4. **Citation Tracking**: Every claim must reference source chunk

---

## 🛡️ Regulatory Standards Supported

| Standard | Description |
|----------|-------------|
| ISO 10993 | Biocompatibility Testing |
| IEC 62304 | Medical Device Software |
| ISO 14971 | Risk Management |
| ISO 13485 | Quality Management |
| IEC 60601 | Electrical Safety |
| 21 CFR Part 820 | FDA Quality System |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API Key

### Backend Setup
```bash
cd TraceBridge
python -m venv venv
.\venv\Scripts\activate        # Windows
source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

---

## 📡 API Reference

### POST /upload
Upload and index a document.

**Request:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf" \
  -F "device_name=CardioSense Pro" \
  -F "doc_type=vnv"
```

**Response:**
```json
{
  "doc_id": "abc123",
  "filename": "document.pdf",
  "chunks_indexed": 45,
  "standards_detected": ["IEC 62304", "ISO 14971"]
}
```

### POST /query
RAG query with citations.

**Request:**
```json
{
  "query": "What verification tests were performed?",
  "device_name": "CardioSense Pro",
  "top_k": 5
}
```

**Response:**
```json
{
  "success": true,
  "answer": "The submission includes...",
  "citations": [
    {
      "chunk_id": "chunk_12",
      "snippet": "...",
      "relevance_score": 0.89,
      "page_number": 5
    }
  ],
  "fallback_used": false
}
```

### POST /gap-report
Generate gap analysis report.

**Request:**
```json
{
  "device_name": "CardioSense Pro",
  "focus_area": "V&V"
}
```

**Response:**
```json
{
  "success": true,
  "device_name": "CardioSense Pro",
  "gaps": [
    {
      "category": "V&V",
      "severity": "critical",
      "fda_requirement": "Software unit testing",
      "evidence_found": null,
      "gap_description": "No unit test documentation",
      "remediation_steps": ["Add unit test reports"]
    }
  ],
  "total_gaps": 3
}
```

---

## 🎨 Frontend Architecture

### Component Hierarchy
```
App
├── Header (navigation)
├── Routes
│   ├── Landing (hero + features)
│   ├── Upload (form + file upload)
│   ├── Analysis (progress + API calls)
│   ├── Results (gaps + actions)
│   └── Documentation (API docs)
└── Modals
    ├── GapDetailModal (3-column analysis)
    └── RemediationPlanModal (saved items)
```

### State Management
- **Component State**: React useState for UI
- **Session Storage**: Persists workflow data between pages
  - `analysisData`: Device info, doc IDs, standards
  - `gapReport`: Gap analysis results
  - `queryResult`: RAG query response
  - `remediationPlan`: Saved gap items
  - `acknowledgedGaps`: User acknowledgments

### Design System
- **Colors**: Primary blue (#1a4b8c), gradient to teal (#00b894)
- **Typography**: Inter font family
- **Effects**: Glassmorphism, smooth animations
- **Responsive**: Mobile-first with breakpoints

---

## 🔒 Security Considerations

1. **API Key Protection**: Never expose OpenAI key to frontend
2. **File Validation**: Check file types and sizes
3. **Input Sanitization**: Validate all user inputs
4. **CORS**: Configured for development origins

---

## 📊 Performance Optimizations

1. **Chunking**: Balanced size for retrieval accuracy
2. **Vector Indexing**: Persistent ChromaDB storage
3. **Lazy Loading**: Frontend components loaded on demand
4. **Session Storage**: Avoid redundant API calls

---

## 🧪 Testing

### Backend
```bash
pytest tests/ -v
```

### API Health Check
```bash
curl http://localhost:8000/health
```

---

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `LLM_MODEL` | GPT model name | gpt-4o-mini |
| `CHROMA_PERSIST_DIR` | Vector DB path | ./chroma_data |
| `UPLOAD_DIR` | File storage path | ./uploads |
| `CHUNK_SIZE` | Characters per chunk | 500 |
| `CHUNK_OVERLAP` | Overlap size | 100 |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 and embeddings
- ChromaDB for vector storage
- FastAPI for the backend framework
- React + Vite for the frontend

---

**Built with ❤️ for regulatory compliance professionals**
