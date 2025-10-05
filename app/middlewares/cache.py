"""
Response caching middleware for FastAPI.
"""

import hashlib
import json
from typing import Callable, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.constants import ENABLE_RESPONSE_CACHING, RESPONSE_CACHE_TTL
from app.core.redis_cache import redis_cache


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware for caching API responses.
    """

    def __init__(self, app):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
        """
        super().__init__(app)
        self.cache_enabled = ENABLE_RESPONSE_CACHING

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and cache responses when appropriate.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            Response: The API response
        """
        # Skip caching for non-GET requests
        if not self.cache_enabled or request.method != "GET":
            return await call_next(request)
            
        # Skip caching for certain paths
        path = request.url.path
        if path.startswith(("/docs", "/redoc", "/openapi.json", "/metrics")):
            return await call_next(request)
            
        # Generate cache key from request path and query parameters
        cache_key = self._generate_cache_key(request)
        
        # Try to get response from cache
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=dict(cached_response["headers"]),
                media_type=cached_response["media_type"]
            )
            
        # Process the request
        response = await call_next(request)
        
        # Cache the response if it's successful
        if 200 <= response.status_code < 300:
            await self._cache_response(cache_key, response)
            
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate a unique cache key for the request.
        
        Args:
            request: The incoming request
            
        Returns:
            str: A unique cache key
        """
        # Get the full URL including query parameters
        url = str(request.url)
        
        # Create a hash of the URL
        return f"response_cache:{hashlib.md5(url.encode()).hexdigest()}"
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """
        Get a cached response.
        
        Args:
            cache_key: The cache key
            
        Returns:
            Optional[Dict]: The cached response or None
        """
        return redis_cache.get(cache_key)
    
    async def _cache_response(self, cache_key: str, response: Response) -> None:
        """
        Cache a response.
        
        Args:
            cache_key: The cache key
            response: The response to cache
        """
        # Read response body
        response_body = [section async for section in response.body_iterator]
        response.body_iterator = iter(response_body)
        content = b"".join(response_body)
        
        # Prepare response data for caching
        response_data = {
            "content": content,
            "status_code": response.status_code,
            "headers": dict(response.headers.items()),
            "media_type": response.media_type
        }
        
        # Cache the response
        redis_cache.set(cache_key, response_data, RESPONSE_CACHE_TTL)
