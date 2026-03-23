from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    learnable_ollama_url: str = "http://localhost:11434"
    learnable_model_gateway_mode: str = "mock"
    learnable_model_gateway_mock_fallback: bool = True
    learnable_model_planner: str = "qwen3:0.6b"
    learnable_model_synthesizer: str = "gemma3:1b"
    learnable_model_synthesizer_fallback: str = "llama3.2:1b"
    learnable_model_embedding: str = "qwen3-embedding:0.6b"
    learnable_reranker_model: str = "bge-reranker-v2-m3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
