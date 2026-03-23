from __future__ import annotations

import re
from collections import Counter
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app import models, schemas
from app.cache import get_cache
from app.config import get_settings
from app.service_clients import embed_texts

settings = get_settings()
cache = get_cache()


def lexical_score(query: str, text: str) -> float:
    terms = [term for term in re.findall(r"[a-zA-Z0-9]+", query.lower()) if len(term) > 2]
    if not terms:
        return 0.0
    counts = Counter(re.findall(r"[a-zA-Z0-9]+", text.lower()))
    raw = sum(counts.get(term, 0) for term in terms)
    return float(raw) / max(len(text.split()), 1)


def _collection_url() -> str:
    return f"{settings.learnable_qdrant_url}/collections/{settings.learnable_qdrant_collection}"


def ensure_collection(dimension: int) -> bool:
    try:
        with httpx.Client(timeout=settings.learnable_request_timeout_seconds) as client:
            existing = client.get(_collection_url())
            if existing.status_code == 200:
                return True
            response = client.put(
                _collection_url(),
                json={"vectors": {"size": dimension, "distance": "Cosine"}},
            )
            response.raise_for_status()
            return True
    except Exception:
        return False


def index_chunks(chunks: list[models.Chunk]) -> bool:
    if not chunks:
        return True
    vectors = embed_texts([chunk.text for chunk in chunks])
    if not vectors:
        return False
    if not ensure_collection(len(vectors[0])):
        return False
    points = [
        {
            "id": chunk.id,
            "vector": vector,
            "payload": {
                "workspace_id": chunk.workspace_id,
                "document_id": chunk.document_id,
                "section": chunk.section,
                "citation": chunk.citation,
                "text": chunk.text,
            },
        }
        for chunk, vector in zip(chunks, vectors, strict=False)
    ]
    try:
        with httpx.Client(timeout=max(30, settings.learnable_request_timeout_seconds)) as client:
            response = client.put(
                f"{_collection_url()}/points",
                params={"wait": "true"},
                json={"points": points},
            )
            response.raise_for_status()
            return True
    except Exception:
        return False


def vector_search(workspace_id: str, query: str, limit: int) -> list[dict[str, Any]] | None:
    query_vector = embed_texts([query])
    if not query_vector:
        return None
    try:
        with httpx.Client(timeout=max(30, settings.learnable_request_timeout_seconds)) as client:
            response = client.post(
                f"{_collection_url()}/points/search",
                json={
                    "vector": query_vector[0],
                    "limit": limit,
                    "with_payload": True,
                    "filter": {
                        "must": [
                            {
                                "key": "workspace_id",
                                "match": {"value": workspace_id},
                            }
                        ]
                    },
                },
            )
            response.raise_for_status()
            body = response.json()
            return body.get("result", [])
    except Exception:
        return None


def search_workspace_chunks(db: Session, workspace_id: str, body: schemas.SearchRequest) -> schemas.SearchResponse:
    cache_key = f"search:{workspace_id}:{body.query}:{body.limit}"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return schemas.SearchResponse(**cached)

    results: list[schemas.SearchResult] = []
    vector_hits = vector_search(workspace_id, body.query, body.limit)
    if vector_hits:
        chunk_ids = [str(hit["id"]) for hit in vector_hits]
        chunks = (
            db.query(models.Chunk)
            .filter(models.Chunk.workspace_id == workspace_id, models.Chunk.id.in_(chunk_ids))
            .all()
        )
        chunk_map = {chunk.id: chunk for chunk in chunks}
        for hit in vector_hits:
            chunk = chunk_map.get(str(hit["id"]))
            if chunk is None:
                continue
            results.append(
                schemas.SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    workspace_id=chunk.workspace_id,
                    text=chunk.text,
                    citation=chunk.citation,
                    score=round(float(hit.get("score", 0.0)), 4),
                )
            )

    if not results:
        chunks = (
            db.query(models.Chunk)
            .filter(models.Chunk.workspace_id == workspace_id)
            .order_by(models.Chunk.created_at.asc())
            .all()
        )
        ranked = sorted(chunks, key=lambda chunk: lexical_score(body.query, chunk.text), reverse=True)
        results = [
            schemas.SearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                workspace_id=chunk.workspace_id,
                text=chunk.text,
                citation=chunk.citation,
                score=round(lexical_score(body.query, chunk.text), 4),
            )
            for chunk in ranked[: body.limit]
            if lexical_score(body.query, chunk.text) > 0
        ]

    response = schemas.SearchResponse(query=body.query, results=results)
    cache.set_json(cache_key, response.model_dump(mode="json"))
    return response


def retrieve_chunks_for_query(
    db: Session,
    workspace_id: str,
    query: str,
    limit: int = 6,
) -> list[tuple[models.Chunk, float]]:
    response = search_workspace_chunks(
        db,
        workspace_id,
        schemas.SearchRequest(query=query, limit=limit),
    )
    if not response.results:
        return []
    chunk_ids = [result.chunk_id for result in response.results]
    chunks = (
        db.query(models.Chunk)
        .filter(models.Chunk.workspace_id == workspace_id, models.Chunk.id.in_(chunk_ids))
        .all()
    )
    chunk_map = {chunk.id: chunk for chunk in chunks}
    ordered_results: list[tuple[models.Chunk, float]] = []
    for result in response.results:
        chunk = chunk_map.get(result.chunk_id)
        if chunk is not None:
            ordered_results.append((chunk, result.score))
    return ordered_results
