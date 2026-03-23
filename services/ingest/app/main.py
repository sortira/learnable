from __future__ import annotations

import re
from typing import Any

from fastapi import FastAPI

from app.config import get_settings
from app.schemas import ChunkRead, ParseTextRequest, ParseTextResponse

settings = get_settings()
app = FastAPI(title="Learnable Ingest Service", version="0.1.0")


def clean_text(text: str) -> str:
    compact = re.sub(r"\r\n?", "\n", text)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    return compact.strip()


def structure_aware_chunks(markdown: str, title: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current_section = title or "Overview"
    buffer: list[str] = []

    def flush() -> None:
        text = clean_text("\n".join(buffer))
        if text:
            sections.append({"section": current_section, "text": text})

    for line in markdown.splitlines():
        if line.startswith("#"):
            flush()
            current_section = line.lstrip("#").strip() or current_section
            buffer = []
            continue
        buffer.append(line)
    flush()

    chunks: list[dict[str, Any]] = []
    for section in sections or [{"section": title or "Overview", "text": markdown}]:
        chunk_buffer: list[str] = []
        current_words = 0
        chunk_index = 0
        for paragraph in [part for part in section["text"].split("\n\n") if part.strip()]:
            size = len(paragraph.split())
            if chunk_buffer and current_words + size > settings.learnable_ingest_chunk_word_budget:
                chunks.append(
                    {
                        "section": section["section"],
                        "text": clean_text("\n\n".join(chunk_buffer)),
                        "chunk_index": chunk_index,
                    }
                )
                chunk_buffer = [paragraph]
                current_words = size
                chunk_index += 1
            else:
                chunk_buffer.append(paragraph)
                current_words += size
        if chunk_buffer:
            chunks.append(
                {
                    "section": section["section"],
                    "text": clean_text("\n\n".join(chunk_buffer)),
                    "chunk_index": chunk_index,
                }
            )
    return chunks


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "learnable-ingest"}


@app.post("/v1/parse/text", response_model=ParseTextResponse)
def parse_text(body: ParseTextRequest) -> ParseTextResponse:
    markdown = clean_text(body.text)
    chunks = [ChunkRead(**chunk) for chunk in structure_aware_chunks(markdown, body.title)]
    return ParseTextResponse(
        title=body.title,
        markdown=markdown,
        structure={"format": "text", "title": body.title},
        chunks=chunks,
    )
