"""
Redis cache module for storing and retrieving models and embeddings.
"""

import json
import logging
import pickle
import time
from typing import Any, Dict, Optional, Union

import redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.constants import (
    DEFAULT_REDIS_CACHE_TTL,
    DEFAULT_REDIS_NAMESPACE,
    DEFAULT_REDIS_URL,
    DEFAULT_SOCKET_CONNECT_TIMEOUT,
    DEFAULT_SOCKET_TIMEOUT,
)

# Set up logging
logger = logging.getLogger(__name__)

# Default expiration time (24 hours in seconds)
DEFAULT_EXPIRATION = DEFAULT_REDIS_CACHE_TTL

# Redis connection pool
_redis_pool = None


def get_redis_client() -> redis.Redis:
    """
    Get a Redis client instance from the connection pool.

    Returns:
        redis.Redis: A Redis client instance
    """
    global _redis_pool

    # Get Redis configuration from settings
    redis_url = getattr(settings, "REDIS_URL", DEFAULT_REDIS_URL)

    # Create connection pool if it doesn't exist
    if _redis_pool is None:
        try:
            _redis_pool = redis.ConnectionPool.from_url(
                redis_url,
                decode_responses=False,  # Don't decode responses for binary data
                socket_timeout=DEFAULT_SOCKET_TIMEOUT,
                socket_connect_timeout=DEFAULT_SOCKET_CONNECT_TIMEOUT,
                retry_on_timeout=True,
            )
            logger.info(f"Redis connection pool initialized with URL: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection pool: {e}")
            return None

    # Get client from pool
    try:
        return redis.Redis(connection_pool=_redis_pool)
    except Exception as e:
        logger.error(f"Failed to get Redis client from pool: {e}")
        return None


class RedisCache:
    """
    Redis-based cache for storing and retrieving models and embeddings.
    """

    def __init__(self, namespace: str = DEFAULT_REDIS_NAMESPACE):
        """
        Initialize the Redis cache.

        Args:
            namespace (str): Namespace for cache keys
        """
        self.namespace = namespace
        self.client = get_redis_client()
        self.enabled = self.client is not None

        if not self.enabled:
            logger.warning("Redis cache is disabled because Redis client couldn't be initialized")

    def _get_key(self, key: str) -> str:
        """
        Get the full Redis key with namespace.

        Args:
            key (str): The cache key

        Returns:
            str: The full Redis key
        """
        return f"{self.namespace}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key (str): The cache key

        Returns:
            Any: The cached value or None if not found
        """
        if not self.enabled:
            return None

        full_key = self._get_key(key)

        try:
            # Get the value from Redis
            value = self.client.get(full_key)

            if value is None:
                return None

            # Deserialize the value
            return pickle.loads(value)
        except (RedisError, pickle.PickleError) as e:
            logger.error(f"Error getting value from Redis cache: {e}")
            return None

    def set(self, key: str, value: Any, expiration: int = DEFAULT_EXPIRATION) -> bool:
        """
        Set a value in the cache.

        Args:
            key (str): The cache key
            value (Any): The value to cache
            expiration (int): Expiration time in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False

        full_key = self._get_key(key)

        try:
            # Serialize the value
            serialized_value = pickle.dumps(value)

            # Set the value in Redis with expiration
            return self.client.setex(full_key, expiration, serialized_value)
        except (RedisError, pickle.PickleError) as e:
            logger.error(f"Error setting value in Redis cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key (str): The cache key

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False

        full_key = self._get_key(key)

        try:
            return bool(self.client.delete(full_key))
        except RedisError as e:
            logger.error(f"Error deleting value from Redis cache: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key (str): The cache key

        Returns:
            bool: True if the key exists, False otherwise
        """
        if not self.enabled:
            return False

        full_key = self._get_key(key)

        try:
            return bool(self.client.exists(full_key))
        except RedisError as e:
            logger.error(f"Error checking key existence in Redis cache: {e}")
            return False

    def set_with_metadata(
        self, key: str, value: Any, metadata: Dict[str, Any], expiration: int = DEFAULT_EXPIRATION
    ) -> bool:
        """
        Set a value in the cache with metadata.

        Args:
            key (str): The cache key
            value (Any): The value to cache
            metadata (Dict[str, Any]): Metadata to store alongside the value
            expiration (int): Expiration time in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False

        # Create a wrapper object with the value and metadata
        wrapper = {"value": value, "metadata": metadata, "timestamp": time.time()}

        return self.set(key, wrapper, expiration)

    def get_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value and its metadata from the cache.

        Args:
            key (str): The cache key

        Returns:
            Dict[str, Any]: A dictionary with 'value' and 'metadata' keys, or None if not found
        """
        if not self.enabled:
            return None

        wrapper = self.get(key)

        if wrapper is None or not isinstance(wrapper, dict):
            return None

        return wrapper

    def clear_namespace(self) -> int:
        """
        Clear all keys in the current namespace.

        Returns:
            int: Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            # Get all keys in the namespace
            pattern = f"{self.namespace}:*"
            keys = self.client.keys(pattern)

            if not keys:
                return 0

            # Delete all keys
            return self.client.delete(*keys)
        except RedisError as e:
            logger.error(f"Error clearing namespace in Redis cache: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict[str, Any]: Cache statistics
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            # Get all keys in the namespace
            pattern = f"{self.namespace}:*"
            keys = self.client.keys(pattern)

            # Get memory usage
            memory_usage = sum(self.client.memory_usage(key) or 0 for key in keys)

            return {
                "enabled": True,
                "key_count": len(keys),
                "memory_usage_bytes": memory_usage,
                "memory_usage_mb": round(memory_usage / (1024 * 1024), 2) if memory_usage else 0,
            }
        except RedisError as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {"enabled": True, "error": str(e)}


# Create global cache instance
redis_cache = RedisCache()
