"""Redis-based caching for translation results."""
import hashlib
import json
import logging
from typing import Optional, Dict, Any

import redis

from config import settings

logger = logging.getLogger(__name__)


class TranslationCache:
    """Redis cache for translation results."""
    
    def __init__(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            self.redis_client.ping()
            self.ttl = 86400  # 24 hours
            self.hits = 0
            self.misses = 0
            logger.info("Redis cache initialized successfully")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
    
    def _generate_key(self, text: str) -> str:
        """Generate cache key from text hash."""
        return f"translation:{hashlib.sha256(text.encode()).hexdigest()}"
    
    def get(self, text: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached translation result."""
        if not self.redis_client:
            return None
        
        try:
            key = self._generate_key(text)
            cached = self.redis_client.get(key)
            
            if cached:
                self.hits += 1
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(cached)
            else:
                self.misses += 1
                logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, text: str, result: Dict[str, Any]) -> None:
        """Store translation result in cache."""
        if not self.redis_client:
            return
        
        try:
            key = self._generate_key(text)
            self.redis_client.setex(key, self.ttl, json.dumps(result))
            logger.debug(f"Cached result for key: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "connected": self.redis_client is not None
        }


# Global cache instance
cache = TranslationCache()
