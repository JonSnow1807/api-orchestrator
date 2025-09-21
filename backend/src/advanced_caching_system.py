"""
Advanced Caching System for API Orchestrator
Multi-tier caching with Redis, memory, and intelligent cache invalidation
"""

from typing import Optional, Dict, Any, List, Set, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import hashlib
import pickle
import time
import logging
from contextlib import asynccontextmanager
import weakref
from collections import OrderedDict, defaultdict

# Optional imports with graceful fallbacks
try:
    import aioredis
    HAS_REDIS = True
except ImportError:
    aioredis = None
    HAS_REDIS = False

try:
    import memcache
    HAS_MEMCACHED = True
except ImportError:
    memcache = None
    HAS_MEMCACHED = False

from src.config import settings

class CacheLevel(str, Enum):
    L1_MEMORY = "l1_memory"  # Local in-memory cache
    L2_REDIS = "l2_redis"    # Redis distributed cache
    L3_MEMCACHED = "l3_memcached"  # Memcached cluster
    L4_DATABASE = "l4_database"    # Database-backed cache

class CacheStrategy(str, Enum):
    LRU = "lru"              # Least Recently Used
    LFU = "lfu"              # Least Frequently Used
    TTL = "ttl"              # Time To Live
    ADAPTIVE = "adaptive"     # AI-powered adaptive caching
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"

class InvalidationStrategy(str, Enum):
    TTL_BASED = "ttl_based"
    EVENT_BASED = "event_based"
    PATTERN_BASED = "pattern_based"
    DEPENDENCY_BASED = "dependency_based"
    AI_PREDICTED = "ai_predicted"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    tags: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    compression_ratio: float = 1.0
    hit_rate: float = 0.0

@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    memory_usage_bytes: int = 0
    compression_ratio: float = 1.0
    avg_response_time_ms: float = 0.0
    hit_rate_by_level: Dict[CacheLevel, float] = field(default_factory=dict)
    popular_keys: List[str] = field(default_factory=list)

class LRUCache:
    """Thread-safe LRU cache implementation"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.stats = CacheStats()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[CacheEntry]:
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                entry.accessed_at = datetime.utcnow()
                entry.access_count += 1
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.stats.cache_hits += 1
                return entry
            else:
                self.stats.cache_misses += 1
                return None

    async def set(self, key: str, entry: CacheEntry):
        async with self._lock:
            if key in self.cache:
                # Update existing entry
                self.cache[key] = entry
                self.cache.move_to_end(key)
            else:
                # Add new entry
                if len(self.cache) >= self.max_size:
                    # Remove least recently used
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    self.stats.evictions += 1

                self.cache[key] = entry

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def clear(self):
        async with self._lock:
            self.cache.clear()

    async def size(self) -> int:
        return len(self.cache)

class RedisCache:
    """Redis-based distributed cache"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.stats = CacheStats()

    async def connect(self):
        """Connect to Redis"""
        if HAS_REDIS:
            try:
                self.redis_client = await aioredis.from_url(self.redis_url)
                await self.redis_client.ping()
                logging.info("✅ Connected to Redis")
            except Exception as e:
                logging.warning(f"⚠️ Redis connection failed: {e}")
                self.redis_client = None

    async def get(self, key: str) -> Optional[CacheEntry]:
        if not self.redis_client:
            return None

        try:
            data = await self.redis_client.get(key)
            if data:
                entry_dict = json.loads(data)
                entry = CacheEntry(
                    key=key,
                    value=entry_dict['value'],
                    created_at=datetime.fromisoformat(entry_dict['created_at']),
                    accessed_at=datetime.utcnow(),
                    access_count=entry_dict.get('access_count', 0) + 1,
                    ttl_seconds=entry_dict.get('ttl_seconds'),
                    size_bytes=entry_dict.get('size_bytes', 0),
                    tags=set(entry_dict.get('tags', [])),
                    dependencies=set(entry_dict.get('dependencies', []))
                )
                self.stats.cache_hits += 1

                # Update access count in Redis
                await self._update_access_stats(key, entry)
                return entry
            else:
                self.stats.cache_misses += 1
                return None
        except Exception as e:
            logging.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, entry: CacheEntry, ttl_seconds: Optional[int] = None):
        if not self.redis_client:
            return

        try:
            entry_dict = {
                'value': entry.value,
                'created_at': entry.created_at.isoformat(),
                'access_count': entry.access_count,
                'ttl_seconds': entry.ttl_seconds,
                'size_bytes': entry.size_bytes,
                'tags': list(entry.tags),
                'dependencies': list(entry.dependencies)
            }

            data = json.dumps(entry_dict)

            if ttl_seconds or entry.ttl_seconds:
                await self.redis_client.setex(
                    key,
                    ttl_seconds or entry.ttl_seconds,
                    data
                )
            else:
                await self.redis_client.set(key, data)

        except Exception as e:
            logging.error(f"Redis set error: {e}")

    async def delete(self, key: str) -> bool:
        if not self.redis_client:
            return False

        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logging.error(f"Redis delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str):
        """Clear keys matching pattern"""
        if not self.redis_client:
            return

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            logging.error(f"Redis clear pattern error: {e}")

    async def _update_access_stats(self, key: str, entry: CacheEntry):
        """Update access statistics"""
        try:
            stats_key = f"stats:{key}"
            await self.redis_client.hincrby(stats_key, "access_count", 1)
            await self.redis_client.hset(stats_key, "last_accessed", datetime.utcnow().isoformat())
        except Exception as e:
            logging.debug(f"Stats update error: {e}")

class AdvancedCacheManager:
    """Multi-tier cache manager with intelligent strategies"""

    def __init__(self):
        self.l1_cache = LRUCache(max_size=10000)  # 10K entries in memory
        self.l2_cache = RedisCache()
        self.l3_cache = None  # Memcached (optional)

        self.global_stats = CacheStats()
        self.invalidation_rules = defaultdict(list)
        self.compression_threshold = 1024  # Compress entries > 1KB
        self.adaptive_weights = {
            CacheLevel.L1_MEMORY: 1.0,
            CacheLevel.L2_REDIS: 0.8,
            CacheLevel.L3_MEMCACHED: 0.6
        }

        # Performance monitoring
        self.performance_history = []
        self.hot_keys = set()
        self.cold_keys = set()

    async def initialize(self):
        """Initialize cache connections"""
        await self.l2_cache.connect()

        if HAS_MEMCACHED:
            try:
                self.l3_cache = memcache.Client(['127.0.0.1:11211'])
                logging.info("✅ Connected to Memcached")
            except Exception as e:
                logging.warning(f"⚠️ Memcached connection failed: {e}")

    def _generate_cache_key(self, namespace: str, key: str, **kwargs) -> str:
        """Generate standardized cache key"""
        key_parts = [namespace, key]

        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            key_suffix = hashlib.md5(
                json.dumps(sorted_kwargs, sort_keys=True).encode()
            ).hexdigest()[:8]
            key_parts.append(key_suffix)

        return ":".join(key_parts)

    def _compress_value(self, value: Any) -> bytes:
        """Compress large values"""
        import gzip

        serialized = pickle.dumps(value)
        if len(serialized) > self.compression_threshold:
            compressed = gzip.compress(serialized)
            return compressed
        return serialized

    def _decompress_value(self, data: bytes) -> Any:
        """Decompress cached values"""
        import gzip

        try:
            # Try decompressing first
            decompressed = gzip.decompress(data)
            return pickle.loads(decompressed)
        except:
            # Fallback to direct pickle loading
            return pickle.loads(data)

    async def get(
        self,
        namespace: str,
        key: str,
        default: Any = None,
        **kwargs
    ) -> Any:
        """Get value from multi-tier cache"""
        cache_key = self._generate_cache_key(namespace, key, **kwargs)
        start_time = time.time()

        # L1: Memory cache
        entry = await self.l1_cache.get(cache_key)
        if entry:
            self._record_hit(CacheLevel.L1_MEMORY, time.time() - start_time)
            return entry.value

        # L2: Redis cache
        entry = await self.l2_cache.get(cache_key)
        if entry:
            # Promote to L1
            await self.l1_cache.set(cache_key, entry)
            self._record_hit(CacheLevel.L2_REDIS, time.time() - start_time)
            return entry.value

        # L3: Memcached (if available)
        if self.l3_cache:
            try:
                data = self.l3_cache.get(cache_key)
                if data:
                    value = self._decompress_value(data)

                    # Create entry and promote
                    entry = CacheEntry(
                        key=cache_key,
                        value=value,
                        created_at=datetime.utcnow(),
                        accessed_at=datetime.utcnow(),
                        access_count=1
                    )

                    await self.l1_cache.set(cache_key, entry)
                    await self.l2_cache.set(cache_key, entry)

                    self._record_hit(CacheLevel.L3_MEMCACHED, time.time() - start_time)
                    return value
            except Exception as e:
                logging.debug(f"L3 cache error: {e}")

        self._record_miss(time.time() - start_time)
        return default

    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        strategy: CacheStrategy = CacheStrategy.LRU,
        **kwargs
    ):
        """Set value in multi-tier cache"""
        cache_key = self._generate_cache_key(namespace, key, **kwargs)

        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            value=value,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            access_count=1,
            ttl_seconds=ttl_seconds,
            size_bytes=len(str(value).encode()),
            tags=tags or set()
        )

        # Set in all cache levels
        await self.l1_cache.set(cache_key, entry)
        await self.l2_cache.set(cache_key, entry, ttl_seconds)

        if self.l3_cache:
            try:
                compressed_data = self._compress_value(value)
                self.l3_cache.set(cache_key, compressed_data, time=ttl_seconds or 3600)
            except Exception as e:
                logging.debug(f"L3 cache set error: {e}")

        # Add invalidation rules
        if tags:
            for tag in tags:
                self.invalidation_rules[tag].append(cache_key)

    async def delete(self, namespace: str, key: str, **kwargs):
        """Delete from all cache levels"""
        cache_key = self._generate_cache_key(namespace, key, **kwargs)

        await self.l1_cache.delete(cache_key)
        await self.l2_cache.delete(cache_key)

        if self.l3_cache:
            try:
                self.l3_cache.delete(cache_key)
            except Exception as e:
                logging.debug(f"L3 cache delete error: {e}")

    async def invalidate_by_tag(self, tag: str):
        """Invalidate all cache entries with specific tag"""
        if tag in self.invalidation_rules:
            keys_to_delete = self.invalidation_rules[tag]

            for cache_key in keys_to_delete:
                await self.l1_cache.delete(cache_key)
                await self.l2_cache.delete(cache_key)

                if self.l3_cache:
                    try:
                        self.l3_cache.delete(cache_key)
                    except Exception as e:
                        logging.debug(f"L3 cache delete error: {e}")

            # Clear invalidation rules for this tag
            del self.invalidation_rules[tag]

    async def invalidate_by_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        await self.l2_cache.clear_pattern(pattern)

        # For L1 cache, we need to iterate and check
        l1_keys_to_delete = []
        async with self.l1_cache._lock:
            for key in self.l1_cache.cache.keys():
                if pattern.replace('*', '') in key:
                    l1_keys_to_delete.append(key)

        for key in l1_keys_to_delete:
            await self.l1_cache.delete(key)

    def _record_hit(self, level: CacheLevel, response_time: float):
        """Record cache hit statistics"""
        self.global_stats.total_requests += 1
        self.global_stats.cache_hits += 1

        if level not in self.global_stats.hit_rate_by_level:
            self.global_stats.hit_rate_by_level[level] = 0

        # Update hit rate for level
        current_hits = self.global_stats.hit_rate_by_level[level]
        self.global_stats.hit_rate_by_level[level] = (current_hits + 1) / self.global_stats.total_requests

        # Update average response time
        current_avg = self.global_stats.avg_response_time_ms
        self.global_stats.avg_response_time_ms = (
            (current_avg * (self.global_stats.total_requests - 1) + response_time * 1000) /
            self.global_stats.total_requests
        )

    def _record_miss(self, response_time: float):
        """Record cache miss statistics"""
        self.global_stats.total_requests += 1
        self.global_stats.cache_misses += 1

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        l1_size = await self.l1_cache.size()

        overall_hit_rate = (
            self.global_stats.cache_hits / self.global_stats.total_requests
            if self.global_stats.total_requests > 0 else 0
        )

        return {
            "overall_hit_rate": overall_hit_rate,
            "total_requests": self.global_stats.total_requests,
            "cache_hits": self.global_stats.cache_hits,
            "cache_misses": self.global_stats.cache_misses,
            "avg_response_time_ms": self.global_stats.avg_response_time_ms,
            "hit_rate_by_level": self.global_stats.hit_rate_by_level,
            "l1_cache_size": l1_size,
            "l1_max_size": self.l1_cache.max_size,
            "invalidation_rules_count": len(self.invalidation_rules),
            "hot_keys_count": len(self.hot_keys),
            "cold_keys_count": len(self.cold_keys)
        }

    async def optimize_cache_performance(self):
        """AI-powered cache optimization"""
        stats = await self.get_stats()

        # Adjust cache sizes based on hit rates
        if stats["hit_rate_by_level"].get(CacheLevel.L1_MEMORY, 0) < 0.7:
            # Increase L1 cache size
            self.l1_cache.max_size = min(self.l1_cache.max_size * 1.2, 50000)

        # Identify hot and cold keys for better placement
        # This would analyze access patterns and adjust caching strategy

        # Adaptive TTL adjustment based on access patterns
        # Implementation would analyze access frequency and adjust TTLs

        logging.info(f"Cache optimization completed. Hit rate: {stats['overall_hit_rate']:.2%}")

# Decorators for easy caching integration

def cached(
    namespace: str = "default",
    ttl_seconds: Optional[int] = 3600,
    tags: Optional[Set[str]] = None,
    strategy: CacheStrategy = CacheStrategy.LRU
):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = await cache_manager.get(namespace, cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(
                namespace, cache_key, result,
                ttl_seconds=ttl_seconds, tags=tags, strategy=strategy
            )
            return result

        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we'll need to handle differently
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            # This would require a synchronous cache interface
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

# Global cache manager instance
cache_manager = AdvancedCacheManager()

# Specialized cache helpers
class APIResponseCache:
    """Specialized cache for API responses"""

    @staticmethod
    async def get_api_response(endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached API response"""
        return await cache_manager.get(
            "api_responses",
            endpoint,
            **params
        )

    @staticmethod
    async def cache_api_response(
        endpoint: str,
        params: Dict[str, Any],
        response: Any,
        ttl_seconds: int = 300
    ):
        """Cache API response"""
        await cache_manager.set(
            "api_responses",
            endpoint,
            response,
            ttl_seconds=ttl_seconds,
            tags={"api_cache"},
            **params
        )

class DatabaseQueryCache:
    """Specialized cache for database queries"""

    @staticmethod
    async def get_query_result(query_hash: str) -> Optional[Any]:
        """Get cached database query result"""
        return await cache_manager.get("db_queries", query_hash)

    @staticmethod
    async def cache_query_result(
        query_hash: str,
        result: Any,
        ttl_seconds: int = 600,
        tables: Optional[Set[str]] = None
    ):
        """Cache database query result"""
        tags = {"db_cache"}
        if tables:
            tags.update(f"table:{table}" for table in tables)

        await cache_manager.set(
            "db_queries",
            query_hash,
            result,
            ttl_seconds=ttl_seconds,
            tags=tags
        )

    @staticmethod
    async def invalidate_table_cache(table_name: str):
        """Invalidate all cached queries for a table"""
        await cache_manager.invalidate_by_tag(f"table:{table_name}")

# Performance monitoring integration
class CachePerformanceMonitor:
    """Monitor cache performance and provide insights"""

    def __init__(self, cache_manager: AdvancedCacheManager):
        self.cache_manager = cache_manager
        self.monitoring_enabled = True

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive cache performance report"""
        stats = await self.cache_manager.get_stats()

        # Calculate efficiency metrics
        efficiency_score = stats["overall_hit_rate"] * 100

        # Performance recommendations
        recommendations = []
        if stats["overall_hit_rate"] < 0.7:
            recommendations.append("Consider increasing cache TTL for frequently accessed data")
        if stats["avg_response_time_ms"] > 10:
            recommendations.append("Optimize cache storage or consider using faster cache backend")
        if stats["l1_cache_size"] >= stats["l1_max_size"] * 0.9:
            recommendations.append("Consider increasing L1 cache size")

        return {
            "performance_score": efficiency_score,
            "statistics": stats,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def monitor_real_time(self, duration_seconds: int = 60):
        """Monitor cache performance in real-time"""
        start_time = time.time()
        monitoring_data = []

        while time.time() - start_time < duration_seconds and self.monitoring_enabled:
            stats = await self.cache_manager.get_stats()
            monitoring_data.append({
                "timestamp": datetime.utcnow().isoformat(),
                "hit_rate": stats["overall_hit_rate"],
                "response_time": stats["avg_response_time_ms"],
                "total_requests": stats["total_requests"]
            })

            await asyncio.sleep(5)  # Sample every 5 seconds

        return monitoring_data

# Initialize global cache manager
async def initialize_cache_system():
    """Initialize the advanced caching system"""
    await cache_manager.initialize()
    logging.info("🚀 Advanced caching system initialized")

# Cache warming utilities
async def warm_cache_with_popular_data():
    """Pre-populate cache with frequently accessed data"""
    # This would be implemented based on usage analytics
    # Pre-load popular API endpoints, user data, etc.
    pass