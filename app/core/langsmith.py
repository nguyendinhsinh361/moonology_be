"""
LangSmith client module.
"""

import logging

from langchain.callbacks.tracers.langchain import LangChainTracer
from langsmith import Client

from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)


def get_langsmith_client():
    """
    Get a LangSmith client instance.

    Returns:
        Client: A LangSmith client instance or None if API key is not set
    """
    if not settings.LANGSMITH_API_KEY:
        logger.debug("LangSmith API key not set, returning None")
        return None

    try:
        client = Client(
            api_key=settings.LANGSMITH_API_KEY,
            api_url=settings.LANGSMITH_ENDPOINT,
        )
        return client
    except Exception as e:
        logger.warning(f"Error creating LangSmith client: {str(e)}")
        return None


def get_langsmith_tracer(run_name=None):
    """
    Get a LangSmith tracer for LangChain callbacks.

    Args:
        run_name (str, optional): Name for tracing runs

    Returns:
        LangChainTracer: A LangChain tracer instance or None if tracing is disabled
    """
    if not settings.LANGSMITH_TRACING or not settings.LANGSMITH_API_KEY:
        return None

    try:
        client = get_langsmith_client()
        if not client:
            return None

        # Use tags instead of run_name in newer versions if available
        tags = [run_name] if run_name else None

        tracer_kwargs = {
            "project_name": settings.LANGSMITH_PROJECT,
            "client": client,
        }

        # Some versions support run_name, others don't, so try both approaches
        try:
            return LangChainTracer(**tracer_kwargs, run_name=run_name)
        except TypeError:
            # If run_name is not supported, try with tags
            return LangChainTracer(**tracer_kwargs, tags=tags)
    except Exception as e:
        logger.warning(f"Failed to create LangSmith tracer: {str(e)}")
        return None
