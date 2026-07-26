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
