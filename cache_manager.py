import redis
import json
from typing import Optional, Dict, Any
from cachetools import TTLCache
import os
from dotenv import load_dotenv

load_dotenv()

class MultiLevelCache:
    def __init__(self):
        # L1 Cache: In-memory TTL cache (fastest, ~0.1ms)
        self.l1_cache_size = int(os.getenv("L1_CACHE_SIZE", 1000))
        self.l1_cache_ttl = int(os.getenv("L1_CACHE_TTL", 300))  # 5 minutes
        self.l2_cache_ttl = int(os.getenv("L2_CACHE_TTL", 3600))  # 1 hour
        
        self.enable_l1 = os.getenv("ENABLE_L1_CACHE", "true").lower() == "true"
        self.enable_l2 = os.getenv("ENABLE_L2_CACHE", "true").lower() == "true"
        
        # Initialize L1 Cache (in-memory)
        if self.enable_l1:
            self.l1_cache = TTLCache(maxsize=self.l1_cache_size, ttl=self.l1_cache_ttl)
        else:
            self.l1_cache = None
        
        # Initialize L2 Cache (Redis - shared across users)
        self.redis_client = None
        if self.enable_l2:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection with fallback handling"""
        try:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                print("✅ Connected to Redis L2 Cache (Shared Translation Pool)")
            else:
                print("⚠️ No Redis URL provided, L2 cache disabled")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, text: str, target_language: str) -> str:
        """Generate consistent cache key for shared translations"""
        return f"translation:{hash(text.lower().strip())}:{target_language.lower()}"
    
    async def get(self, text: str, target_language: str) -> Optional[Dict[str, Any]]:
        """Get translation from multi-level cache (shared across all users)"""
        cache_key = self._generate_cache_key(text, target_language)
        
        # Try L1 Cache first (fastest, ~0.1ms)
        if self.l1_cache and cache_key in self.l1_cache:
            result = self.l1_cache[cache_key]
            result["cache_level"] = "L1"
            return result
        
        # Try L2 Cache (Redis - shared translation pool, ~20-50ms)
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    result = json.loads(cached_data)
                    # Populate L1 cache for future requests
                    if self.l1_cache:
                        self.l1_cache[cache_key] = result
                    result["cache_level"] = "L2"
                    return result
            except Exception as e:
                print(f"⚠️ L2 cache read error: {e}")
        
        return None
    
    async def set(self, text: str, target_language: str, translation_data: Dict[str, Any]):
        """Store translation in shared cache (benefits all users)"""
        cache_key = self._generate_cache_key(text, target_language)
        
        # Store in L1 Cache (in-memory)
        if self.l1_cache:
            self.l1_cache[cache_key] = translation_data.copy()
        
        # Store in L2 Cache (Redis - shared pool)
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key, 
                    self.l2_cache_ttl, 
                    json.dumps(translation_data, ensure_ascii=False)
                )
            except Exception as e:
                print(f"⚠️ L2 cache write error: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "l1_enabled": self.enable_l1,
            "l2_enabled": self.enable_l2 and self.redis_client is not None,
            "l1_size": len(self.l1_cache) if self.l1_cache else 0,
            "l1_maxsize": self.l1_cache_size if self.l1_cache else 0,
        }
        
        if self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats["l2_connected"] = True
                stats["l2_memory_used"] = redis_info.get("used_memory_human", "N/A")
                stats["l2_total_keys"] = self.redis_client.dbsize()
            except:
                stats["l2_connected"] = False
        else:
            stats["l2_connected"] = False
            
        return stats

# Global cache instance
cache_manager = MultiLevelCache()
