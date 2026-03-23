from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    learnable_env: str = "development"
    learnable_log_level: str = "INFO"
    learnable_api_host: str = "0.0.0.0"
    learnable_api_port: int = 8000
    learnable_database_url: str = "sqlite+pysqlite:///./learnable.db"
    learnable_storage_root: str = "./data"
    learnable_redis_url: str = "redis://localhost:6379/0"
    learnable_qdrant_url: str = "http://localhost:6333"
    learnable_qdrant_collection: str = "learnable_chunks"
    learnable_ingest_url: str = "http://localhost:8100"
    learnable_orchestrator_url: str = "http://localhost:8200"
    learnable_model_gateway_url: str = "http://localhost:8300"
    learnable_cache_ttl_seconds: int = 300
    learnable_max_recursion_depth: int = 3
    learnable_max_spawned_nodes: int = 12
    learnable_max_evidence_per_node: int = 8
    learnable_max_tokens_per_run: int = 120000
    learnable_max_runtime_seconds: int = 600
    learnable_max_upload_bytes: int = 10 * 1024 * 1024
    learnable_request_timeout_seconds: int = 20
    learnable_http_user_agent: str = "Learnable/0.1"

    @property
    def storage_root(self) -> Path:
        root = Path(self.learnable_storage_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    @property
    def object_root(self) -> Path:
        path = self.storage_root / "objects"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
