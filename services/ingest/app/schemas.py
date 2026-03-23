from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ParseTextRequest(BaseModel):
    title: str
    text: str


class ChunkRead(BaseModel):
    section: str
    text: str
    chunk_index: int


class ParseTextResponse(BaseModel):
    title: str
    markdown: str
    structure: dict[str, Any] = Field(default_factory=dict)
    chunks: list[ChunkRead] = Field(default_factory=list)
