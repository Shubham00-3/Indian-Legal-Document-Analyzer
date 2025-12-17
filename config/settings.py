# settings.py
# Centralized configuration management

import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load environment variables
load_dotenv()


@dataclass
class Settings:
    """Application settings loaded from environment variables"""
    
    # Groq API
    groq_api_key: str = ""
    groq_model_name: str = "llama-3.3-70b-versatile"
    
    # Pinecone
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = ""
    
    # Embedding model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    def __post_init__(self):
        """Load settings from environment variables"""
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_model_name = os.getenv("GROQ_MODEL_NAME", "llama3-70b-8192")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "")
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate that all required settings are present"""
        errors = []
        
        if not self.groq_api_key:
            errors.append("GROQ_API_KEY is not set")
        if not self.pinecone_api_key:
            errors.append("PINECONE_API_KEY is not set")
        if not self.pinecone_environment:
            errors.append("PINECONE_ENVIRONMENT is not set")
        if not self.pinecone_index_name:
            errors.append("PINECONE_INDEX_NAME is not set")
        
        return len(errors) == 0, errors


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
