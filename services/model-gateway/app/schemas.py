from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ModelRole(str, Enum):
    plan = "plan"
    classify = "classify"
    rewrite_query = "rewrite_query"
    embed = "embed"
    rerank = "rerank"
    synthesize = "synthesize"
    generate_quiz = "generate_quiz"
    generate_flashcards = "generate_flashcards"


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class GenerateRequest(BaseModel):
    role: ModelRole
    messages: list[ChatMessage]
    temperature: float = 0.2
    max_tokens: int = 512
    use_cache: bool = True
    schema_name: str | None = None


class GenerateResponse(BaseModel):
    role: ModelRole
    provider: str
    model: str
    mode: str
    output_text: str
    latency_ms: int
    cached: bool = False


class EmbedRequest(BaseModel):
    inputs: list[str] = Field(default_factory=list, min_length=1)
    normalize: bool = True


class EmbedResponse(BaseModel):
    provider: str
    model: str
    dimensions: int
    vectors: list[list[float]]


class ModelDescriptor(BaseModel):
    role: ModelRole
    primary_model: str
    fallback_model: str | None = None


class ModelCatalogResponse(BaseModel):
    mode: str
    models: list[ModelDescriptor]
