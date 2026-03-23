from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()


def parse_text_via_ingest(title: str, text: str) -> dict[str, Any] | None:
    try:
        with httpx.Client(timeout=settings.learnable_request_timeout_seconds) as client:
            response = client.post(
                f"{settings.learnable_ingest_url}/v1/parse/text",
                json={"title": title, "text": text},
            )
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


def create_plan(query: str) -> dict[str, Any] | None:
    try:
        with httpx.Client(timeout=settings.learnable_request_timeout_seconds) as client:
            response = client.post(
                f"{settings.learnable_orchestrator_url}/v1/plan",
                json={"query": query, "max_subquestions": min(8, settings.learnable_max_spawned_nodes)},
            )
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


def reflect_on_evidence(query: str, evidence_summaries: list[str]) -> dict[str, Any] | None:
    try:
        with httpx.Client(timeout=settings.learnable_request_timeout_seconds) as client:
            response = client.post(
                f"{settings.learnable_orchestrator_url}/v1/reflect",
                json={"query": query, "evidence_summaries": evidence_summaries},
            )
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


def generate_text(role: str, messages: list[dict[str, str]], max_tokens: int = 512) -> dict[str, Any] | None:
    try:
        with httpx.Client(timeout=max(30, settings.learnable_request_timeout_seconds)) as client:
            response = client.post(
                f"{settings.learnable_model_gateway_url}/v1/generate",
                json={
                    "role": role,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "use_cache": True,
                },
            )
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


def embed_texts(inputs: list[str]) -> list[list[float]] | None:
    try:
        with httpx.Client(timeout=max(30, settings.learnable_request_timeout_seconds)) as client:
            response = client.post(
                f"{settings.learnable_model_gateway_url}/v1/embed",
                json={"inputs": inputs, "normalize": True},
            )
            response.raise_for_status()
            body = response.json()
            return body.get("vectors", [])
    except Exception:
        return None
