"""
Application configuration module.
"""

import os
from typing import List, Optional

import dotenv
from pydantic import BaseModel

from app.core.constants import (
    DEFAULT_LANGSMITH_ENDPOINT,
    DEFAULT_LANGSMITH_PROJECT,
    DEFAULT_MODEL_PROVIDER,
    DEFAULT_REDIS_CACHE_TTL,
    DEFAULT_REDIS_NAMESPACE,
)

dotenv.load_dotenv()


class Settings(BaseModel):
    """Application settings."""

    # App settings
    APP_NAME: str = "Moonology Chatbot API"
    APP_DESCRIPTION: str = "A chatbot API built with LangChain, LangGraph, and FastAPI"
    APP_VERSION: str = "0.1.0"

    # API settings
    API_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = ["*"]  # In production, replace with specific origins

    # Database settings
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME")

    # LLM API settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY: Optional[str] = "AIzaSyBxJvMZ_zt3w_8NL95MuC8e6jRTHWkfMU4" or os.getenv(
        "GOOGLE_API_KEY"
    )
    DEFAULT_MODEL_PROVIDER: str = os.getenv("DEFAULT_MODEL_PROVIDER", DEFAULT_MODEL_PROVIDER)


    # LangSmith settings
    LANGSMITH_API_KEY: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", DEFAULT_LANGSMITH_PROJECT)
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", DEFAULT_LANGSMITH_ENDPOINT)

    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL")
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED")
    REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", DEFAULT_REDIS_CACHE_TTL))
    REDIS_NAMESPACE: str = os.getenv("REDIS_NAMESPACE", DEFAULT_REDIS_NAMESPACE)

    # Cache settings
    CACHE_EMBEDDINGS: bool = os.getenv("CACHE_EMBEDDINGS", "true").lower() == "true"
    CACHE_MODELS: bool = os.getenv("CACHE_MODELS", "true").lower() == "true"
    CACHE_GRAPHS: bool = os.getenv("CACHE_GRAPHS", "true").lower() == "true"
    
    # Frontend settings
    NEXT_PUBLIC_BACKEND_URL: str = os.getenv("NEXT_PUBLIC_BACKEND_URL")

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "forbid"}


# Create global settings instance
settings = Settings()
