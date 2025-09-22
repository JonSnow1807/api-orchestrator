"""
Redis caching and performance optimization for API Orchestrator
Implements intelligent caching for API responses, AI analysis, and database queries
"""

# Optional Redis import - graceful fallback to memory cache
try:
    import redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from functools import wraps
import logging
import os
import pickle

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager with intelligent TTL and compression"""

    def __init__(self):
        # Redis connection with fallback to memory cache
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self._memory_cache = {}  # Fallback in-memory cache

        if HAS_REDIS and redis:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,  # We'll handle encoding ourselves
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                self.redis_client.ping()
                self.use_redis = True
                logger.info("✅ Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"⚠️ Redis unavailable, using memory cache: {e}")
                self.use_redis = False
        else:
            logger.info("⚠️ Redis module not installed, using memory cache")
            self.use_redis = False

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from inputs"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return f"api_orch:{hashlib.md5(key_data.encode()).hexdigest()}"

    def _serialize(self, data: Any) -> bytes:
        """Serialize data with compression for storage"""
        try:
            # Use pickle for complex objects, JSON for simple ones
            if isinstance(data, (dict, list, str, int, float, bool, type(None))):
                return json.dumps(data).encode("utf-8")
            else:
                return pickle.dumps(data)
        except Exception:
            return pickle.dumps(data)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        try:
            # Try JSON first (faster)
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None

        try:
            if self.use_redis:
                data = self.redis_client.get(key)
                if data:
                    return self._deserialize(data)
            else:
                # Memory cache fallback
                if key in self._memory_cache:
                    item = self._memory_cache[key]
                    if item["expires"] > datetime.now():
                        return item["data"]
                    else:
                        del self._memory_cache[key]
        except Exception as e:
            logger.error(f"Cache get error: {e}")

        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)"""
        if not self.enabled:
            return False

        try:
            serialized_data = self._serialize(value)

            if self.use_redis:
                return self.redis_client.setex(key, ttl, serialized_data)
            else:
                # Memory cache fallback with TTL
                self._memory_cache[key] = {
                    "data": value,
                    "expires": datetime.now() + timedelta(seconds=ttl),
                }
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.use_redis:
                return bool(self.redis_client.delete(key))
            else:
                return self._memory_cache.pop(key, None) is not None
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            if self.use_redis:
                keys = self.redis_client.keys(f"api_orch:{pattern}*")
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # Clear memory cache matching pattern
                to_delete = [
                    k
                    for k in self._memory_cache.keys()
                    if k.startswith(f"api_orch:{pattern}")
                ]
                for key in to_delete:
                    del self._memory_cache[key]
                return len(to_delete)
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
        return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.use_redis:
                info = self.redis_client.info()
                return {
                    "type": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "hit_rate": round(
                        (
                            info.get("keyspace_hits", 0)
                            / max(
                                1,
                                info.get("keyspace_hits", 0)
                                + info.get("keyspace_misses", 0),
                            )
                        )
                        * 100,
                        2,
                    ),
                }
            else:
                return {
                    "type": "memory",
                    "keys": len(self._memory_cache),
                    "status": "active",
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"type": "error", "message": str(e)}


# Global cache instance
cache = CacheManager()

# Decorators for easy caching


def cached(ttl: int = 3600, key_prefix: str = "func"):
    """Decorator to cache function results"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )

            # Try to get from cache first
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result

            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


def cached_async(ttl: int = 3600, key_prefix: str = "async_func"):
    """Async decorator to cache function results"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )

            # Try to get from cache first
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for async {func.__name__}")
                return result

            # Execute function and cache result
            logger.debug(f"Cache miss for async {func.__name__}, executing...")
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


# Specialized cache keys for different data types


class CacheKeys:
    """Predefined cache key patterns for consistency"""

    # API Analysis caching
    AI_ANALYSIS = "ai_analysis"
    API_RESPONSE = "api_response"

    # Database query caching
    USER_PROJECTS = "user_projects"
    PROJECT_APIS = "project_apis"
    USER_PROFILE = "user_profile"

    # OpenAPI spec processing
    SPEC_PARSING = "spec_parsing"
    SPEC_VALIDATION = "spec_validation"

    # Mock server responses
    MOCK_RESPONSE = "mock_response"

    # Authentication
    USER_PERMISSIONS = "user_permissions"

    @staticmethod
    def user_specific(user_id: int, key_type: str) -> str:
        """Generate user-specific cache key"""
        return f"user:{user_id}:{key_type}"

    @staticmethod
    def project_specific(project_id: int, key_type: str) -> str:
        """Generate project-specific cache key"""
        return f"project:{project_id}:{key_type}"


# Cache warming functions


def warm_user_cache(user_id: int, db_session):
    """Pre-warm cache with user's commonly accessed data"""
    from src.database import DatabaseManager

    try:
        # Cache user projects
        projects = DatabaseManager.get_user_projects(db_session, user_id)
        cache.set(
            cache._generate_key(CacheKeys.USER_PROJECTS, user_id),
            [p.to_dict() for p in projects],
            ttl=1800,  # 30 minutes
        )

        # Cache user profile
        user = DatabaseManager.get_user_by_id(db_session, user_id)
        if user:
            cache.set(
                cache._generate_key(CacheKeys.USER_PROFILE, user_id),
                user.to_dict(),
                ttl=3600,  # 1 hour
            )

        logger.info(f"✅ Warmed cache for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to warm cache for user {user_id}: {e}")


def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a user"""
    patterns = [f"user:{user_id}", f"*user_id*{user_id}*"]

    total_deleted = 0
    for pattern in patterns:
        total_deleted += cache.clear_pattern(pattern)

    logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")


# Performance monitoring cache decorator


def performance_cached(ttl: int = 3600):
    """Cache with performance monitoring"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            cache_key = cache._generate_key(f"perf:{func.__name__}", *args, **kwargs)

            # Try cache first
            result = cache.get(cache_key)
            if result is not None:
                cache_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"⚡ Cache hit for {func.__name__} in {cache_time:.3f}s")
                return result

            # Execute and time
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()

            # Cache result
            cache.set(cache_key, result, ttl)
            logger.info(f"🔄 Executed {func.__name__} in {execution_time:.3f}s")

            return result

        return wrapper

    return decorator


if __name__ == "__main__":
    # Test cache functionality
    print("🧪 Testing cache functionality...")

    # Test basic operations
    cache.set("test_key", {"message": "Hello Cache!"}, 60)
    result = cache.get("test_key")
    print(f"Cache test result: {result}")

    # Test decorator
    @cached(ttl=30, key_prefix="test")
    def expensive_function(x, y):
        import time

        time.sleep(0.1)  # Simulate expensive operation
        return x * y + 42

    print("Testing decorator...")
    start = datetime.now()
    result1 = expensive_function(5, 10)
    time1 = (datetime.now() - start).total_seconds()

    start = datetime.now()
    result2 = expensive_function(5, 10)  # Should be cached
    time2 = (datetime.now() - start).total_seconds()

    print(f"First call: {result1} in {time1:.3f}s")
    print(f"Cached call: {result2} in {time2:.3f}s")
    print(f"Speedup: {time1/time2:.1f}x")

    # Get cache stats
    stats = cache.get_stats()
    print(f"Cache stats: {json.dumps(stats, indent=2)}")
