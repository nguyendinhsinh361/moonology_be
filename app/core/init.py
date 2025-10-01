"""
Application initialization module.
"""

import logging
import os

from app.core.config import settings
from app.core.constants import DEFAULT_TEMPERATURE
from app.core.langsmith import get_langsmith_client
from app.core.redis_cache import redis_cache
from app.repositories.mongodb import get_mongodb_client

# Set up logging
logger = logging.getLogger(__name__)

# Global cache for models and embeddings (fallback if Redis is not available)
_MEMORY_CACHE = {}


def init_application():
    """
    Initialize the application, setting up database connections and LangSmith tracing.

    Returns:
        bool: True if initialization was successful
    """
    # Connect to MongoDB to verify the connection
    get_mongodb_client()



    # Clear LangChain environment variables to prevent automatic tracing
    # We'll handle tracing directly through our own code
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_TRACING", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)

    # Enable LangSmith tracing if configured
    if settings.LANGSMITH_TRACING:
        if not settings.LANGSMITH_API_KEY:
            logger.warning("LangSmith tracing is enabled but LANGSMITH_API_KEY is not set.")
        else:
            try:
                # Initialize LangSmith client to verify connection
                langsmith_client = get_langsmith_client()
                if langsmith_client:
                    # Check if project exists, create if it doesn't
                    init_langsmith_project(langsmith_client)

                    logger.info(
                        f"LangSmith tracing is enabled for project: {settings.LANGSMITH_PROJECT}"
                    )

                    # Set environment variables for LangChain
                    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
            except Exception as e:
                logger.error(f"Failed to initialize LangSmith client: {e}")
    else:
        logger.info("LangSmith tracing is disabled.")

    # Initialize Redis cache
    init_redis_cache()

    # Pre-initialize models and embeddings
    preload_models_and_embeddings()

    logger.info("Application initialized successfully.")
    return True




def init_langsmith_project(client):
    """
    Initialize LangSmith project if it doesn't exist.

    Args:
        client: LangSmith client instance
    """
    try:
        # Get list of projects
        projects = client.list_projects()
        project_names = [project.name for project in projects]

        # Create project if it doesn't exist
        if settings.LANGSMITH_PROJECT not in project_names:
            logger.info(f"Creating LangSmith project: {settings.LANGSMITH_PROJECT}")
            client.create_project(settings.LANGSMITH_PROJECT)
            logger.info(f"Created LangSmith project: {settings.LANGSMITH_PROJECT}")
        else:
            logger.info(f"LangSmith project already exists: {settings.LANGSMITH_PROJECT}")
    except Exception as e:
        logger.error(f"Failed to initialize LangSmith project: {e}")
        logger.info("Continuing without LangSmith project initialization")


def init_redis_cache():
    """
    Initialize Redis cache and check connection.
    """
    if not settings.REDIS_ENABLED:
        logger.info("Redis cache is disabled in settings.")
        return

    # Check if Redis is available
    if redis_cache.enabled:
        # Set namespace from settings
        redis_cache.namespace = settings.REDIS_NAMESPACE

        # Log cache statistics
        stats = redis_cache.get_stats()
        logger.info(f"Redis cache initialized: {stats}")
    else:
        logger.warning("Redis cache is not available. Using in-memory cache as fallback.")


def preload_models_and_embeddings():
    """
    Preload and cache models and embeddings to reduce initialization time on first API call.
    """
    if (
        not settings.CACHE_EMBEDDINGS
        and not settings.CACHE_MODELS
    ):
        logger.info("Model caching is disabled. Skipping preloading.")
        return

    try:
        # Preload embedding model if enabled
        if settings.CACHE_EMBEDDINGS:
            logger.info("Preloading embedding model...")
            # Import here to avoid circular imports
            from app.models.embedding import get_embeddings

            # Get the embedding model
            embeddings = get_embeddings()

            # Cache the embedding model
            if redis_cache.enabled:
                redis_cache.set("embeddings", embeddings, settings.REDIS_CACHE_TTL)
            else:
                _MEMORY_CACHE["embeddings"] = embeddings

            logger.info("Embedding model preloaded successfully")


        # Preload LLM models if enabled and API keys are available
        if settings.CACHE_MODELS:
            if settings.DEFAULT_MODEL_PROVIDER == "gemini" and settings.GOOGLE_API_KEY:
                logger.info("Preloading Gemini model...")
                from app.enum.model import ModelGeminiName
                from app.models.llm_models import get_gemini_model

                # Get the model with default settings
                gemini_model = get_gemini_model(
                    model_name=ModelGeminiName.GEMINI_2_5_FLASH_LITE,
                    temperature=DEFAULT_TEMPERATURE,
                    run_name="preloaded-gemini",
                )

                # Cache the model
                if redis_cache.enabled:
                    redis_cache.set("gemini_model", gemini_model, settings.REDIS_CACHE_TTL)
                else:
                    _MEMORY_CACHE["gemini_model"] = gemini_model

                logger.info("Gemini model preloaded successfully")

            elif settings.DEFAULT_MODEL_PROVIDER == "openai" and settings.OPENAI_API_KEY:
                logger.info("Preloading OpenAI model...")
                from app.enum.model import ModelOpenAiName
                from app.models.llm_models import get_openai_model

                # Get the model with default settings
                openai_model = get_openai_model(
                    model_name=ModelOpenAiName.OPENAI_GPT_5_NANO,
                    run_name="preloaded-openai",
                )

                # Cache the model
                if redis_cache.enabled:
                    redis_cache.set("openai_model", openai_model, settings.REDIS_CACHE_TTL)
                else:
                    _MEMORY_CACHE["openai_model"] = openai_model

                logger.info("OpenAI model preloaded successfully")

    except Exception as e:
        logger.error(f"Error preloading models: {e}")
        logger.info("Continuing without preloaded models")


def get_cached_model(key):
    """
    Get a cached model or embedding.
    First tries Redis cache, then falls back to memory cache if Redis is not available.

    Args:
        key: Cache key

    Returns:
        The cached object or None if not found
    """
    # Try Redis cache first if enabled
    if redis_cache.enabled:
        cached_value = redis_cache.get(key)
        if cached_value is not None:
            return cached_value

    # Fall back to memory cache
    return _MEMORY_CACHE.get(key)
