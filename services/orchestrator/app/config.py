from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    learnable_max_recursion_depth: int = 3
    learnable_max_spawned_nodes: int = 12
    learnable_max_evidence_per_node: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
