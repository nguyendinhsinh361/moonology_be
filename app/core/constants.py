"""
Constants module for the HSK Chatbot application.

This module contains all the constant values used throughout the application.
"""

# Default LLM parameters
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 200
DEFAULT_MAX_TOKENS_GRAPH = 5000

# Redis cache settings
DEFAULT_REDIS_NAMESPACE = "moonology"
DEFAULT_REDIS_CACHE_TTL = 86400  # 24 hours in seconds
DEFAULT_REDIS_URL = "redis://redis:6379/0"

# Vector search settings
DEFAULT_SIMILARITY_THRESHOLD = 0.3

# Socket settings
DEFAULT_SOCKET_TIMEOUT = 5
DEFAULT_SOCKET_CONNECT_TIMEOUT = 5

# Server settings
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_RELOAD = True

# LangSmith settings
DEFAULT_LANGSMITH_PROJECT = "moonology"
DEFAULT_LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"

# Default model provider
DEFAULT_MODEL_PROVIDER = "openai"

# Default error message
DEFAULT_ERROR_RESPONSE = "I'm sorry, I couldn't process your request."

# Default embedding model
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
