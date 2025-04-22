from typing import Optional
from pydantic import BaseModel

class CacheConfig(BaseModel):
    """Configuration for cache usage.
    
    Attributes:
        cache_name: Name of the cache to use
        auto_refresh_ttl: Optional TTL to refresh the cache with if it exists
    """
    cache_name: str
    auto_refresh_ttl: Optional[str] = None 

    def __str__(self) -> str:
        return f"CacheConfig(cache_name={self.cache_name}, auto_refresh_ttl={self.auto_refresh_ttl})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CacheConfig):
            return False
        return self.cache_name == other.cache_name and self.auto_refresh_ttl == other.auto_refresh_ttl

    def __hash__(self) -> int:
        return hash((self.cache_name, self.auto_refresh_ttl))