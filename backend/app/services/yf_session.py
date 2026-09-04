"""
Component: Backend -> Services -> Cache
Belongs to: used exclusively by services/market_data.py to cache yfinance responses.
Purpose: a tiny TTL cache with two interchangeable backends — Redis (local/self-hosted
default, CACHE_BACKEND=redis) or an in-process dict (hosted profile,
CACHE_BACKEND=memory, avoiding a Redis dependency on the free tier). Reduces
yfinance calls (which are slow and rate-limit-prone) for repeated requests.
"""

import json
import time
from typing import Any

from app.core.config import get_settings

settings = get_settings()

_use_redis = settings.cache_backend == "redis"
_redis = None
_memory: dict[str, tuple[float, Any]] = {}

if _use_redis:
    import redis

    _redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)


# Reads a cached value, or None on a miss/expiry/error. Never raises — a cache failure
# should degrade to "cache miss", not break the caller.
def cache_get(key: str) -> Any | None:
    if _use_redis:
        try:
            raw = _redis.get(key)
        except Exception:
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    entry = _memory.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if expires_at < time.time():
        _memory.pop(key, None)
        return None
    return value


# Writes a value with a TTL (seconds). The in-memory backend clears itself entirely if
# it grows past 2000 keys — a crude but sufficient bound for a single-instance free-tier
# deployment (no LRU eviction, just a full reset).
def cache_set(key: str, value: Any, ttl: int) -> None:
    if _use_redis:
        try:
            _redis.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception:
            pass
        return

    if len(_memory) > 2000:
        _memory.clear()
    _memory[key] = (time.time() + ttl, value)
