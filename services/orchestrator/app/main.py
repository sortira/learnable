from __future__ import annotations

import re

from fastapi import FastAPI

from app.config import get_settings
from app.schemas import PlanRequest, PlanResponse, ReflectionRequest, ReflectionResponse

settings = get_settings()
app = FastAPI(title="Learnable Orchestrator Service", version="0.1.0")


def derive_sub_questions(query: str, max_subquestions: int) -> list[str]:
    topic = re.sub(r"\s+", " ", query.strip().rstrip("?"))
    defaults = [
        f"What are the foundational concepts behind {topic}?",
        f"Which sources provide the strongest evidence for {topic}?",
        f"What should the user study next to understand {topic} more deeply?",
        f"What contradictions or open questions remain about {topic}?",
    ]
    return defaults[:max_subquestions]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "learnable-orchestrator"}


@app.post("/v1/plan", response_model=PlanResponse)
def create_plan(body: PlanRequest) -> PlanResponse:
    return PlanResponse(
        objective=body.query,
        sub_questions=derive_sub_questions(body.query, body.max_subquestions),
        stop_conditions=[
            "Evidence coverage is sufficient",
            "Contradictions have been surfaced",
            "Configured budget limits were reached",
        ],
        budgets={
            "max_recursion_depth": settings.learnable_max_recursion_depth,
            "max_spawned_nodes": settings.learnable_max_spawned_nodes,
            "max_evidence_per_node": settings.learnable_max_evidence_per_node,
        },
    )


@app.post("/v1/reflect", response_model=ReflectionResponse)
def reflect_on_evidence(body: ReflectionRequest) -> ReflectionResponse:
    gaps: list[str] = []
    if len(body.evidence_summaries) < 2:
        gaps.append("Evidence set is shallow; retrieve more sources.")
    if not any("study" in summary.lower() for summary in body.evidence_summaries):
        gaps.append("Learning guidance is missing from the current evidence set.")
    confidence = max(0.2, min(0.95, 0.35 + len(body.evidence_summaries) * 0.12))
    return ReflectionResponse(
        confidence=round(confidence, 2),
        gaps=gaps,
        recurse=bool(gaps),
    )
