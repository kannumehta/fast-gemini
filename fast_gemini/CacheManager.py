from typing import Dict, Optional
from google import genai
from google.genai import types
from .exceptions import GeminiAPIError

class CacheManager:
    def __init__(self, client: genai.Client):
        """Initialize the cache manager.
        
        Args:
            client: The Gemini client instance
        """
        self.client = client

    def create_cache(self, model: str, content: str, ttl: str = "1h", cache_name: Optional[str] = None) -> str:
        """Create a cache for the given content.
        
        Args:
            model: The model to use for caching
            content: The content to cache
            ttl: Time to live for the cache (default: "1h")
            cache_name: Optional name for the cache. If not provided, a name will be generated.
            
        Returns:
            str: The cache name
            
        Raises:
            GeminiAPIError: If cache creation fails
        """
        try:
            display_name = cache_name or f"cache_{model}"
            cache = self.client.caches.create(
                model=model,
                config=types.CreateCachedContentConfig(
                    display_name=display_name,
                    contents=[content],
                    ttl=ttl
                )
            )
            return cache.name
        except Exception as e:
            raise GeminiAPIError("CACHE_CREATE_ERROR", str(e))

    def delete_cache(self, cache_name: str) -> None:
        """Delete a cache by name.
        
        Args:
            cache_name: The name of the cache to delete
            
        Raises:
            GeminiAPIError: If cache deletion fails
        """
        try:
            self.client.caches.delete(cache_name)
        except Exception as e:
            raise GeminiAPIError("CACHE_DELETE_ERROR", str(e))

    def list_caches(self) -> Dict[str, types.CachedContent]:
        """List all active caches.
        
        Returns:
            Dict[str, types.CachedContent]: Dictionary of cache names to cache objects
            
        Note:
            This returns metadata for all caches, including name, model, display_name,
            usage_metadata, create_time, update_time, and expire_time.
            The actual cached content cannot be retrieved.
        """
        try:
            caches = {}
            for cache in self.client.caches.list():
                caches[cache.name] = cache
            return caches
        except Exception as e:
            raise GeminiAPIError("CACHE_LIST_ERROR", str(e))

    def get_cache(self, cache_name: str) -> Optional[types.CachedContent]:
        """Get a cache by name.
        
        Args:
            cache_name: The name of the cache to get
            
        Returns:
            Optional[types.CachedContent]: The cache object if found, None otherwise
            
        Note:
            This returns metadata for the cache, including name, model, display_name,
            usage_metadata, create_time, update_time, and expire_time.
            The actual cached content cannot be retrieved.
        """
        try:
            return self.client.caches.get(name=cache_name)
        except Exception as e:
            raise GeminiAPIError("CACHE_GET_ERROR", str(e))

    def update_cache_ttl(self, cache_name: str, ttl: str) -> None:
        """Update the TTL of a cache.
        
        Args:
            cache_name: The name of the cache to update
            ttl: New time to live for the cache
            
        Raises:
            GeminiAPIError: If cache update fails
        """
        try:
            self.client.caches.update(
                name=cache_name,
                config=types.UpdateCachedContentConfig(ttl=ttl)
            )
        except Exception as e:
            raise GeminiAPIError("CACHE_UPDATE_ERROR", str(e))

    def get_and_refresh(self, cache_name: str, ttl: str) -> Optional[types.CachedContent]:
        """Get a cache by name and refresh its TTL if it exists.
        
        Args:
            cache_name: The name of the cache to get and refresh
            ttl: New time to live for the cache
            
        Returns:
            Optional[types.CachedContent]: The cache object if found, None otherwise
            
        Raises:
            GeminiAPIError: If cache operations fail
        """
        try:
            cache = self.get_cache(cache_name)
            if cache:
                self.update_cache_ttl(cache_name, ttl)
            return cache
        except Exception as e:
            raise GeminiAPIError("CACHE_REFRESH_ERROR", str(e)) 