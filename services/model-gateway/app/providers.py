from __future__ import annotations

import hashlib
import math
import time

import httpx

from app.config import Settings
from app.schemas import GenerateRequest, GenerateResponse, ModelCatalogResponse, ModelDescriptor, ModelRole


def latest_user_message(request: GenerateRequest) -> str:
    for message in reversed(request.messages):
        if message.role == "user":
            return message.content.strip()
    return request.messages[-1].content.strip() if request.messages else ""


def route_model(role: ModelRole, settings: Settings) -> tuple[str, str | None]:
    if role in {ModelRole.plan, ModelRole.classify, ModelRole.rewrite_query}:
        return settings.learnable_model_planner, None
    if role == ModelRole.embed:
        return settings.learnable_model_embedding, None
    if role == ModelRole.rerank:
        return settings.learnable_reranker_model, None
    return settings.learnable_model_synthesizer, settings.learnable_model_synthesizer_fallback


def catalog(settings: Settings) -> ModelCatalogResponse:
    return ModelCatalogResponse(
        mode=settings.learnable_model_gateway_mode,
        models=[
            ModelDescriptor(role=ModelRole.plan, primary_model=settings.learnable_model_planner),
            ModelDescriptor(role=ModelRole.classify, primary_model=settings.learnable_model_planner),
            ModelDescriptor(role=ModelRole.rewrite_query, primary_model=settings.learnable_model_planner),
            ModelDescriptor(role=ModelRole.embed, primary_model=settings.learnable_model_embedding),
            ModelDescriptor(role=ModelRole.rerank, primary_model=settings.learnable_reranker_model),
            ModelDescriptor(
                role=ModelRole.synthesize,
                primary_model=settings.learnable_model_synthesizer,
                fallback_model=settings.learnable_model_synthesizer_fallback,
            ),
            ModelDescriptor(
                role=ModelRole.generate_quiz,
                primary_model=settings.learnable_model_synthesizer,
                fallback_model=settings.learnable_model_synthesizer_fallback,
            ),
            ModelDescriptor(
                role=ModelRole.generate_flashcards,
                primary_model=settings.learnable_model_synthesizer,
                fallback_model=settings.learnable_model_synthesizer_fallback,
            ),
        ],
    )


def mock_generate(request: GenerateRequest, settings: Settings) -> GenerateResponse:
    started = time.perf_counter()
    prompt = latest_user_message(request)
    if request.role == ModelRole.plan:
        output = (
            "Objective:\n"
            f"- {prompt}\n\n"
            "Sub-questions:\n"
            f"- What are the core concepts behind {prompt}?\n"
            f"- Which sources best support {prompt}?\n"
            f"- What should the user study next about {prompt}?\n\n"
            "Stop conditions:\n"
            "- Evidence is sufficient\n"
            "- Contradictions are resolved\n"
            "- Budget limits are reached"
        )
    elif request.role == ModelRole.rewrite_query:
        output = f"Optimized query: {prompt.lower().strip('?')}"
    elif request.role == ModelRole.classify:
        output = "Classification: research"
    elif request.role == ModelRole.generate_quiz:
        output = f"Quiz draft for: {prompt}"
    elif request.role == ModelRole.generate_flashcards:
        output = f"Flashcard deck draft for: {prompt}"
    else:
        output = (
            "Grounded synthesis draft:\n"
            f"- Focus topic: {prompt}\n"
            "- Use retrieved evidence blocks before making final claims.\n"
            "- Surface remaining gaps explicitly."
        )
    latency_ms = int((time.perf_counter() - started) * 1000)
    model, _fallback = route_model(request.role, settings)
    return GenerateResponse(
        role=request.role,
        provider="mock",
        model=model,
        mode=settings.learnable_model_gateway_mode,
        output_text=output,
        latency_ms=latency_ms,
    )


def ollama_generate(request: GenerateRequest, settings: Settings) -> GenerateResponse:
    started = time.perf_counter()
    model, _fallback = route_model(request.role, settings)
    payload = {
        "model": model,
        "messages": [message.model_dump() for message in request.messages],
        "stream": False,
        "options": {
            "temperature": request.temperature,
            "num_predict": request.max_tokens,
        },
    }
    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{settings.learnable_ollama_url}/api/chat", json=payload)
        response.raise_for_status()
        body = response.json()
    latency_ms = int((time.perf_counter() - started) * 1000)
    output_text = body.get("message", {}).get("content", "").strip()
    return GenerateResponse(
        role=request.role,
        provider="ollama",
        model=model,
        mode=settings.learnable_model_gateway_mode,
        output_text=output_text,
        latency_ms=latency_ms,
    )


def generate(request: GenerateRequest, settings: Settings) -> GenerateResponse:
    if settings.learnable_model_gateway_mode == "mock":
        return mock_generate(request, settings)
    try:
        return ollama_generate(request, settings)
    except Exception:
        if not settings.learnable_model_gateway_mock_fallback:
            raise
        return mock_generate(request, settings)


def hash_embedding(text: str, dimensions: int = 24, normalize: bool = True) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for index in range(dimensions):
        byte = digest[index % len(digest)]
        values.append((byte / 255.0) * 2 - 1)
    if normalize:
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [round(value / norm, 6) for value in values]
    return [round(value, 6) for value in values]


def embed(inputs: list[str], normalize: bool, settings: Settings) -> dict[str, object]:
    if settings.learnable_model_gateway_mode != "mock":
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{settings.learnable_ollama_url}/api/embed",
                    json={
                        "model": settings.learnable_model_embedding,
                        "input": inputs,
                    },
                )
                response.raise_for_status()
                body = response.json()
            return {
                "provider": "ollama",
                "model": settings.learnable_model_embedding,
                "dimensions": len(body["embeddings"][0]) if body.get("embeddings") else 0,
                "vectors": body.get("embeddings", []),
            }
        except Exception:
            if not settings.learnable_model_gateway_mock_fallback:
                raise

    vectors = [hash_embedding(text, normalize=normalize) for text in inputs]
    return {
        "provider": "mock",
        "model": settings.learnable_model_embedding,
        "dimensions": len(vectors[0]) if vectors else 0,
        "vectors": vectors,
    }
