from typing import Optional
from pydantic import BaseModel

class CacheConfig(BaseModel):
    """Configuration for cache usage.
    
    Attributes:
        cache_name: Optional name of the cache to use, uses "cache_{model}" if not provided
        ttl: Optional TTL to refresh the cache with if it exists
        auto_manage_cache: Whether to automatically manage the cache lifecycle
    """
    cache_name: Optional[str] = None
    ttl: Optional[str] = None
    auto_manage_cache: bool = False

    def __str__(self) -> str:
        return f"CacheConfig(cache_name={self.cache_name}, ttl={self.ttl}, auto_manage_cache={self.auto_manage_cache})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CacheConfig):
            return False
        return (self.cache_name == other.cache_name and 
                self.ttl == other.ttl and 
                self.auto_manage_cache == other.auto_manage_cache)

    def __hash__(self) -> int:
        return hash((self.cache_name, self.ttl, self.auto_manage_cache))