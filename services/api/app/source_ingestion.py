from __future__ import annotations

import mimetypes
import re
import tempfile
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from app.config import get_settings
from app.service_clients import parse_text_via_ingest

try:
    from docling.document_converter import DocumentConverter
except Exception:  # pragma: no cover - optional import path for environments without docling
    DocumentConverter = None


settings = get_settings()


def clean_text(text: str) -> str:
    compact = re.sub(r"\r\n?", "\n", text)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    return compact.strip()


def structure_aware_chunks(markdown: str, title: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current_section = "Overview"
    buffer: list[str] = []

    def flush() -> None:
        text = clean_text("\n".join(buffer))
        if not text:
            return
        sections.append({"section": current_section, "text": text})

    for line in markdown.splitlines():
        if line.startswith("#"):
            flush()
            current_section = line.lstrip("#").strip() or current_section
            buffer = []
            continue
        buffer.append(line)
    flush()

    if not sections:
        sections = [{"section": title or "Overview", "text": clean_text(markdown)}]

    chunks: list[dict[str, Any]] = []
    for section in sections:
        paragraphs = [clean_text(p) for p in section["text"].split("\n\n") if clean_text(p)]
        if not paragraphs:
            continue
        chunk_buffer = []
        chunk_index = 0
        current_size = 0
        for paragraph in paragraphs:
            size = len(paragraph.split())
            if chunk_buffer and current_size + size > 160:
                chunks.append(
                    {
                        "section": section["section"],
                        "text": clean_text("\n\n".join(chunk_buffer)),
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1
                chunk_buffer = [paragraph]
                current_size = size
            else:
                chunk_buffer.append(paragraph)
                current_size += size
        if chunk_buffer:
            chunks.append(
                {
                    "section": section["section"],
                    "text": clean_text("\n\n".join(chunk_buffer)),
                    "chunk_index": chunk_index,
                }
            )
    return chunks


def parse_html(content: str, fallback_title: str) -> tuple[str, str, dict[str, Any]]:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = fallback_title
    if soup.title and soup.title.text.strip():
        title = soup.title.text.strip()
    markdown = clean_text(soup.get_text("\n"))
    structure = {"format": "html", "title": title}
    return title, markdown, structure


def parse_text_file(path: Path, fallback_title: str) -> tuple[str, str, dict[str, Any]]:
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    parsed = parse_text_via_ingest(fallback_title, raw_text)
    if parsed is not None:
        return parsed["title"], parsed["markdown"], parsed["structure"]
    markdown = clean_text(raw_text)
    structure = {"format": "text", "title": fallback_title}
    return fallback_title, markdown, structure


def parse_with_docling(source: str | Path, fallback_title: str) -> tuple[str, str, dict[str, Any]]:
    if DocumentConverter is None:
        raise RuntimeError("Docling is not installed in this environment.")
    converter = DocumentConverter()
    result = converter.convert(source)
    markdown = clean_text(result.document.export_to_markdown())
    structure = {"format": "docling", "title": fallback_title}
    return fallback_title, markdown, structure


def ingest_file(path: Path, mime_type: str | None, fallback_title: str) -> dict[str, Any]:
    guessed_mime, _ = mimetypes.guess_type(path.name)
    effective_mime = mime_type or guessed_mime or "application/octet-stream"

    if effective_mime.startswith("text/") or path.suffix.lower() in {".md", ".txt"}:
        title, markdown, structure = parse_text_file(path, fallback_title)
    else:
        title, markdown, structure = parse_with_docling(path, fallback_title)

    chunks = structure_aware_chunks(markdown, title)
    return {"title": title, "markdown": markdown, "structure": structure, "chunks": chunks}


def ingest_url(url: str, fallback_title: str | None = None) -> dict[str, Any]:
    response = requests.get(
        url,
        timeout=settings.learnable_request_timeout_seconds,
        headers={"User-Agent": settings.learnable_http_user_agent},
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    title = fallback_title or url

    if "text/html" in content_type or url.endswith((".html", "/")):
        parsed_title, markdown, structure = parse_html(response.text, title)
        chunks = structure_aware_chunks(markdown, parsed_title)
        return {
            "title": parsed_title,
            "markdown": markdown,
            "structure": {**structure, "url": url},
            "chunks": chunks,
        }

    suffix = Path(url.split("?")[0]).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(response.content)
        temp_path = Path(handle.name)
    try:
        parsed = ingest_file(temp_path, content_type, title)
        parsed["structure"]["url"] = url
        return parsed
    finally:
        temp_path.unlink(missing_ok=True)
