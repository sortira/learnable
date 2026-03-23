from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import Settings, get_settings

try:
    import redis
except Exception:  # pragma: no cover - optional dependency at runtime
    redis = None


class CacheBackend:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._local_cache: dict[str, str] = {}
        self._redis_client = None
        if redis is not None:
            try:
                client = redis.Redis.from_url(settings.learnable_redis_url, decode_responses=True)
                client.ping()
                self._redis_client = client
            except Exception:
                self._redis_client = None

    def get_json(self, key: str) -> Any | None:
        try:
            if self._redis_client is not None:
                payload = self._redis_client.get(key)
            else:
                payload = self._local_cache.get(key)
            return json.loads(payload) if payload else None
        except Exception:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self.settings.learnable_cache_ttl_seconds
        payload = json.dumps(value)
        try:
            if self._redis_client is not None:
                self._redis_client.setex(key, ttl, payload)
            else:
                self._local_cache[key] = payload
        except Exception:
            self._local_cache[key] = payload

    def delete(self, key: str) -> None:
        try:
            if self._redis_client is not None:
                self._redis_client.delete(key)
            else:
                self._local_cache.pop(key, None)
        except Exception:
            self._local_cache.pop(key, None)

    def delete_prefix(self, prefix: str) -> None:
        try:
            if self._redis_client is not None:
                for key in self._redis_client.scan_iter(f"{prefix}*"):
                    self._redis_client.delete(key)
            else:
                for key in list(self._local_cache.keys()):
                    if key.startswith(prefix):
                        self._local_cache.pop(key, None)
        except Exception:
            for key in list(self._local_cache.keys()):
                if key.startswith(prefix):
                    self._local_cache.pop(key, None)


@lru_cache
def get_cache() -> CacheBackend:
    return CacheBackend(get_settings())
