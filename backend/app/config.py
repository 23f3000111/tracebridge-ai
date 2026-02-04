"""
TraceBridge AI - Configuration Management
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    
    # ChromaDB Configuration
    chroma_persist_dir: str = "./chroma_db"
    
    # Upload Configuration
    upload_dir: str = "./data/uploads"
    
    # Chunking Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # ChromaDB Collection Name
    collection_name: str = "tracebridge_documents"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.chroma_persist_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)
    
    @property
    def use_openai_embeddings(self) -> bool:
        """Check if OpenAI embeddings should be used."""
        return (
            self.openai_api_key is not None 
            and self.openai_api_key != "your-openai-api-key-here"
            and len(self.openai_api_key) > 10
        )


# Global settings instance
settings = Settings()
