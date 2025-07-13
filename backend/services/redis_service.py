"""
Redis Caching Service - Phase 8
Handles caching for frequently accessed content with graceful degradation
"""

import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import redis
    from redis.exceptions import ConnectionError, TimeoutError, RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not available. Install with: pip install redis")

from services.init_db import DatabaseManager


@dataclass
class CacheConfig:
    """Configuration for Redis caching"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

    health_check_interval: int = 30
    
    # TTL settings (in seconds)
    chunk_ttl: int = 3600  # 1 hour
    quiz_ttl: int = 1800   # 30 minutes
    objectives_ttl: int = 7200  # 2 hours
    search_results_ttl: int = 900  # 15 minutes
    default_ttl: int = 1800  # 30 minutes


class RedisService:
    """Redis caching service with graceful degradation"""
    
    def __init__(self, config: CacheConfig = None, db_manager: DatabaseManager = None):
        self.config = config or CacheConfig()
        self.db_manager = db_manager
        self.client: Optional[redis.Redis] = None
        self.is_connected = False
        self.last_health_check = 0
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "operations": 0
        }
        
        # Initialize Redis connection
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection with error handling"""
        if not REDIS_AVAILABLE:
            print("⚠️  Redis not available. Caching disabled.")
            return
        
        try:
            self.client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=True
            )
            
            # Test connection
            self.client.ping()
            self.is_connected = True
            self.last_health_check = time.time()
            print("✅ Redis connection established")
            
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("📝 Continuing without cache (graceful degradation)")
            self.client = None
            self.is_connected = False
    
    def _check_health(self) -> bool:
        """Check Redis health with periodic updates"""
        current_time = time.time()
        
        # Only check health if enough time has passed
        if current_time - self.last_health_check < self.config.health_check_interval:
            return self.is_connected
        
        if not self.client:
            return False
        
        try:
            self.client.ping()
            self.is_connected = True
            self.last_health_check = current_time
            return True
        except Exception as e:
            print(f"⚠️  Redis health check failed: {e}")
            self.is_connected = False
            return False
    
    def _safe_operation(self, operation_func, *args, **kwargs):
        """Execute Redis operation with error handling"""
        if not self._check_health():
            return None
        
        try:
            self.stats["operations"] += 1
            result = operation_func(*args, **kwargs)
            return result
        except (ConnectionError, TimeoutError, RedisError) as e:
            print(f"⚠️  Redis operation failed: {e}")
            self.stats["errors"] += 1
            self.is_connected = False
            return None
        except Exception as e:
            print(f"❌ Unexpected Redis error: {e}")
            self.stats["errors"] += 1
            return None
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate consistent cache key"""
        # Hash long identifiers to keep keys manageable
        if len(identifier) > 100:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        return f"quiz_gen:{prefix}:{identifier}"
    
    # Document Chunks Caching
    def cache_chunk(self, chunk_id: str, chunk_data: Dict[str, Any], ttl: int = None) -> bool:
        """Cache a document chunk"""
        if not self.is_connected:
            return False
        
        key = self._generate_key("chunk", chunk_id)
        ttl = ttl or self.config.chunk_ttl
        
        try:
            # Add metadata
            cache_data = {
                **chunk_data,
                "cached_at": datetime.now().isoformat(),
                "cache_type": "chunk"
            }
            
            result = self._safe_operation(
                self.client.setex,
                key,
                ttl,
                json.dumps(cache_data)
            )
            
            return result is not None
            
        except Exception as e:
            print(f"⚠️  Failed to cache chunk {chunk_id}: {e}")
            return False
    
    def get_cached_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached chunk"""
        if not self.is_connected:
            self.stats["misses"] += 1
            return None
        
        key = self._generate_key("chunk", chunk_id)
        
        try:
            result = self._safe_operation(self.client.get, key)
            
            if result:
                self.stats["hits"] += 1
                return json.loads(result)
            else:
                self.stats["misses"] += 1
                return None
                
        except Exception as e:
            print(f"⚠️  Failed to retrieve chunk {chunk_id}: {e}")
            self.stats["misses"] += 1
            return None
    
    def cache_chunks_batch(self, chunks: List[Dict[str, Any]], ttl: int = None) -> int:
        """Cache multiple chunks in batch"""
        if not self.is_connected:
            return 0
        
        ttl = ttl or self.config.chunk_ttl
        cached_count = 0
        
        try:
            pipe = self.client.pipeline()
            
            for chunk in chunks:
                chunk_id = chunk.get("chunk_id") or f"{chunk.get('document_id')}_{chunk.get('chunk_index')}"
                key = self._generate_key("chunk", chunk_id)
                
                cache_data = {
                    **chunk,
                    "cached_at": datetime.now().isoformat(),
                    "cache_type": "chunk"
                }
                
                pipe.setex(key, ttl, json.dumps(cache_data))
            
            results = pipe.execute()
            cached_count = sum(1 for r in results if r)
            
            print(f"✅ Cached {cached_count}/{len(chunks)} chunks")
            return cached_count
            
        except Exception as e:
            print(f"⚠️  Batch chunk caching failed: {e}")
            return 0
    
    # Quiz Caching
    def cache_quiz(self, quiz_id: str, quiz_data: Dict[str, Any], ttl: int = None) -> bool:
        """Cache a generated quiz"""
        if not self.is_connected:
            return False
        
        key = self._generate_key("quiz", quiz_id)
        ttl = ttl or self.config.quiz_ttl
        
        try:
            cache_data = {
                **quiz_data,
                "cached_at": datetime.now().isoformat(),
                "cache_type": "quiz"
            }
            
            result = self._safe_operation(
                self.client.setex,
                key,
                ttl,
                json.dumps(cache_data)
            )
            
            return result is not None
            
        except Exception as e:
            print(f"⚠️  Failed to cache quiz {quiz_id}: {e}")
            return False
    
    def get_cached_quiz(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached quiz"""
        if not self.is_connected:
            self.stats["misses"] += 1
            return None
        
        key = self._generate_key("quiz", quiz_id)
        
        try:
            result = self._safe_operation(self.client.get, key)
            
            if result:
                self.stats["hits"] += 1
                return json.loads(result)
            else:
                self.stats["misses"] += 1
                return None
                
        except Exception as e:
            print(f"⚠️  Failed to retrieve quiz {quiz_id}: {e}")
            self.stats["misses"] += 1
            return None
    
    # Learning Objectives Caching
    def cache_learning_objectives(self, document_id: int, objectives: List[Dict[str, Any]], ttl: int = None) -> bool:
        """Cache learning objectives for a document"""
        if not self.is_connected:
            return False
        
        key = self._generate_key("objectives", str(document_id))
        ttl = ttl or self.config.objectives_ttl
        
        try:
            cache_data = {
                "document_id": document_id,
                "objectives": objectives,
                "cached_at": datetime.now().isoformat(),
                "cache_type": "objectives"
            }
            
            result = self._safe_operation(
                self.client.setex,
                key,
                ttl,
                json.dumps(cache_data)
            )
            
            return result is not None
            
        except Exception as e:
            print(f"⚠️  Failed to cache objectives for document {document_id}: {e}")
            return False
    
    def get_cached_learning_objectives(self, document_id: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached learning objectives"""
        if not self.is_connected:
            self.stats["misses"] += 1
            return None
        
        key = self._generate_key("objectives", str(document_id))
        
        try:
            result = self._safe_operation(self.client.get, key)
            
            if result:
                self.stats["hits"] += 1
                data = json.loads(result)
                return data.get("objectives", [])
            else:
                self.stats["misses"] += 1
                return None
                
        except Exception as e:
            print(f"⚠️  Failed to retrieve objectives for document {document_id}: {e}")
            self.stats["misses"] += 1
            return None
    
    # Search Results Caching
    def cache_search_results(self, query: str, search_type: str, results: List[Dict[str, Any]], ttl: int = None) -> bool:
        """Cache search results"""
        if not self.is_connected:
            return False
        
        # Create cache key from query and search type
        cache_key = f"{query}:{search_type}"
        key = self._generate_key("search", cache_key)
        ttl = ttl or self.config.search_results_ttl
        
        try:
            cache_data = {
                "query": query,
                "search_type": search_type,
                "results": results,
                "cached_at": datetime.now().isoformat(),
                "cache_type": "search_results"
            }
            
            result = self._safe_operation(
                self.client.setex,
                key,
                ttl,
                json.dumps(cache_data)
            )
            
            return result is not None
            
        except Exception as e:
            print(f"⚠️  Failed to cache search results: {e}")
            return False
    
    def get_cached_search_results(self, query: str, search_type: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached search results"""
        if not self.is_connected:
            self.stats["misses"] += 1
            return None
        
        cache_key = f"{query}:{search_type}"
        key = self._generate_key("search", cache_key)
        
        try:
            result = self._safe_operation(self.client.get, key)
            
            if result:
                self.stats["hits"] += 1
                data = json.loads(result)
                return data.get("results", [])
            else:
                self.stats["misses"] += 1
                return None
                
        except Exception as e:
            print(f"⚠️  Failed to retrieve search results: {e}")
            self.stats["misses"] += 1
            return None
    
    # Cache Management
    def invalidate_cache(self, pattern: str = None) -> int:
        """Invalidate cache entries matching pattern"""
        if not self.is_connected:
            return 0
        
        try:
            if pattern:
                # Find keys matching pattern
                keys = self._safe_operation(self.client.keys, f"quiz_gen:{pattern}:*")
                if keys:
                    deleted = self._safe_operation(self.client.delete, *keys)
                    print(f"✅ Invalidated {deleted} cache entries matching '{pattern}'")
                    return deleted or 0
            else:
                # Clear all quiz generator cache
                keys = self._safe_operation(self.client.keys, "quiz_gen:*")
                if keys:
                    deleted = self._safe_operation(self.client.delete, *keys)
                    print(f"✅ Invalidated {deleted} cache entries")
                    return deleted or 0
            
            return 0
            
        except Exception as e:
            print(f"⚠️  Cache invalidation failed: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            **self.stats,
            "is_connected": self.is_connected,
            "last_health_check": self.last_health_check,
            "hit_rate": 0.0
        }
        
        total_requests = stats["hits"] + stats["misses"]
        if total_requests > 0:
            stats["hit_rate"] = stats["hits"] / total_requests
        
        # Add Redis info if connected
        if self.is_connected:
            try:
                redis_info = self._safe_operation(self.client.info, "memory")
                if redis_info:
                    stats["redis_memory"] = {
                        "used_memory": redis_info.get("used_memory", 0),
                        "used_memory_human": redis_info.get("used_memory_human", "0B"),
                        "maxmemory": redis_info.get("maxmemory", 0)
                    }
            except:
                pass
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            "redis_available": REDIS_AVAILABLE,
            "connected": self.is_connected,
            "last_check": self.last_health_check,
            "stats": self.get_cache_stats()
        }
        
        if self.is_connected:
            try:
                # Test basic operations
                test_key = "quiz_gen:health_check"
                self._safe_operation(self.client.set, test_key, "test", ex=10)
                test_result = self._safe_operation(self.client.get, test_key)
                self._safe_operation(self.client.delete, test_key)
                
                health_status["operations_working"] = test_result == "test"
                health_status["status"] = "healthy"
                
            except Exception as e:
                health_status["operations_working"] = False
                health_status["status"] = "unhealthy"
                health_status["error"] = str(e)
        else:
            health_status["status"] = "disconnected"
        
        return health_status
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                self.client.close()
                print("✅ Redis connection closed")
            except:
                pass
        self.is_connected = False


# Utility functions
def create_redis_service(config: Dict[str, Any] = None, db_manager: DatabaseManager = None) -> RedisService:
    """Factory function to create Redis service"""
    if config:
        cache_config = CacheConfig(**config)
    else:
        cache_config = CacheConfig()
    
    return RedisService(cache_config, db_manager) 