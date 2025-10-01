"""
Application initialization module.
"""

import logging
import os

from app.core.config import settings
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
