"""
TraceBridge AI - FastAPI Application
Main application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.routers import documents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="TraceBridge AI",
    description=(
        "A RAG-based backend for FDA 510(k) documentation gap detection. "
        "Upload PDF/DOCX documents, index them for semantic search, and query for insights."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting TraceBridge AI...")
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Log configuration
    if settings.use_openai_embeddings:
        logger.info(f"Using OpenAI embeddings: {settings.embedding_model}")
    else:
        logger.info("Using local embeddings (sentence-transformers)")
    
    logger.info(f"ChromaDB persistence: {settings.chroma_persist_dir}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Chunk size: {settings.chunk_size}, overlap: {settings.chunk_overlap}")
    
    logger.info("TraceBridge AI started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down TraceBridge AI...")


@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": "TraceBridge AI",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "embedding_mode": "openai" if settings.use_openai_embeddings else "local"
    }
