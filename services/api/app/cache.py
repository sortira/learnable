from __future__ import annotations

import json
from functools import lru_cache
from importlib import import_module
from typing import Any

from app.config import Settings, get_settings


class CacheBackend:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._local_cache: dict[str, str] = {}
        self._redis_client: Any | None = None
        self._redis_attempted = False

    def _ensure_redis_client(self) -> Any | None:
        if self._redis_attempted:
            return self._redis_client
        self._redis_attempted = True
        try:
            redis = import_module("redis")
            self._redis_client = redis.Redis.from_url(
                self.settings.learnable_redis_url,
                decode_responses=True,
                socket_connect_timeout=0.25,
                socket_timeout=0.25,
                retry_on_timeout=False,
            )
        except Exception:
            self._redis_client = None
        return self._redis_client

    def get_json(self, key: str) -> Any | None:
        client = self._ensure_redis_client()
        try:
            if client is not None:
                payload = client.get(key)
            else:
                payload = self._local_cache.get(key)
            return json.loads(payload) if payload else None
        except Exception:
            self._redis_client = None
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self.settings.learnable_cache_ttl_seconds
        payload = json.dumps(value)
        client = self._ensure_redis_client()
        try:
            if client is not None:
                client.setex(key, ttl, payload)
            else:
                self._local_cache[key] = payload
        except Exception:
            self._redis_client = None
            self._local_cache[key] = payload

    def delete(self, key: str) -> None:
        client = self._ensure_redis_client()
        try:
            if client is not None:
                client.delete(key)
            else:
                self._local_cache.pop(key, None)
        except Exception:
            self._redis_client = None
            self._local_cache.pop(key, None)

    def delete_prefix(self, prefix: str) -> None:
        client = self._ensure_redis_client()
        try:
            if client is not None:
                for key in client.scan_iter(f"{prefix}*"):
                    client.delete(key)
            else:
                for key in list(self._local_cache.keys()):
                    if key.startswith(prefix):
                        self._local_cache.pop(key, None)
        except Exception:
            self._redis_client = None
            for key in list(self._local_cache.keys()):
                if key.startswith(prefix):
                    self._local_cache.pop(key, None)


@lru_cache
def get_cache() -> CacheBackend:
    return CacheBackend(get_settings())
