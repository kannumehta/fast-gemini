from typing import Dict, Optional, List
from google import genai
from google.genai import types
from .exceptions import GeminiAPIError
from pydantic import BaseModel

class CacheManager(BaseModel):
    def create_cache(self, client: genai.Client, model: str, content: str, ttl: str = "1h", cache_name: Optional[str] = None) -> str:
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
            cache = client.caches.create(
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

    def delete_cache(self, client: genai.Client, cache_name: str) -> str:
        """Delete a cache by name.
        
        Args:
            cache_name: The name of the cache to delete
            
        Returns:
            str: The name of the deleted cache
            
        Raises:
            GeminiAPIError: If cache deletion fails
        """
        try:
            client.caches.delete(cache_name)
            return cache_name
        except Exception as e:
            raise GeminiAPIError("CACHE_DELETE_ERROR", str(e))

    def list_caches(self, client: genai.Client) -> List[str]:
        """List all active caches.
        
        Returns:
            List[str]: List of cache names
            
        Note:
            This returns metadata for all caches, including name, model, display_name,
            usage_metadata, create_time, update_time, and expire_time.
            The actual cached content cannot be retrieved.
        """
        try:
            return [cache.name for cache in client.caches.list()]
        except Exception as e:
            raise GeminiAPIError("CACHE_LIST_ERROR", str(e))

    def get_cache(self, client: genai.Client, cache_name: str) -> Optional[str]:
        """Get a cache by name.
        
        Args:
            cache_name: The name of the cache to get
            
        Returns:
            Optional[str]: The cache name if found, None otherwise
            
        Note:
            This returns metadata for the cache, including name, model, display_name,
            usage_metadata, create_time, update_time, and expire_time.
            The actual cached content cannot be retrieved.
        """
        try:
            cache = client.caches.get(name=cache_name)
            return cache.name if cache else None
        except Exception as e:
            raise GeminiAPIError("CACHE_GET_ERROR", str(e))

    def update_cache_ttl(self, client: genai.Client, cache_name: str, ttl: str) -> str:
        """Update the TTL of a cache.
        
        Args:
            cache_name: The name of the cache to update
            ttl: New time to live for the cache
            
        Returns:
            str: The name of the updated cache
            
        Raises:
            GeminiAPIError: If cache update fails
        """
        try:
            client.caches.update(
                name=cache_name,
                config=types.UpdateCachedContentConfig(ttl=ttl)
            )
            return cache_name
        except Exception as e:
            raise GeminiAPIError("CACHE_UPDATE_ERROR", str(e))

    def create_or_update_cache(self, client: genai.Client, model: str, content: str, ttl: str = "1h", cache_name: Optional[str] = None) -> str:
        """Create a new cache or update an existing one.
        
        Args:
            client: The Gemini client instance
            model: The model to use for caching
            content: The content to cache
            ttl: Time to live for the cache (default: "1h")
            cache_name: Optional name for the cache. If not provided, a name will be generated.
            
        Returns:
            str: The cache name
            
        Raises:
            GeminiAPIError: If cache creation or update fails
        """
        try:
            display_name = cache_name or f"cache_{model}"
            existing_cache = self.get_cache(client, display_name)
            
            if existing_cache:
                # Update existing cache
                return self.update_cache_ttl(client, display_name, ttl)
            else:
                # Create new cache
                return self.create_cache(client, model, content, ttl, display_name)
        except Exception as e:
            raise GeminiAPIError("CACHE_CREATE_OR_UPDATE_ERROR", str(e))

    def get_and_refresh(self, client: genai.Client, cache_name: str, ttl: str) -> Optional[str]:
        """Get a cache by name and refresh its TTL if it exists.
        
        Args:
            cache_name: The name of the cache to get and refresh
            ttl: New time to live for the cache
            
        Returns:
            Optional[str]: The cache name if found and refreshed, None otherwise
            
        Raises:
            GeminiAPIError: If cache operations fail
        """
        try:
            cache = self.get_cache(client, cache_name)
            if cache:
                return self.update_cache_ttl(client, cache_name, ttl)
            return None
        except Exception as e:
            raise GeminiAPIError("CACHE_REFRESH_ERROR", str(e)) 