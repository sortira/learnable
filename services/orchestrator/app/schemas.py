from __future__ import annotations

from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    query: str
    max_subquestions: int = Field(default=3, ge=1, le=8)


class PlanResponse(BaseModel):
    objective: str
    sub_questions: list[str]
    stop_conditions: list[str]
    budgets: dict[str, int]


class ReflectionRequest(BaseModel):
    query: str
    evidence_summaries: list[str] = Field(default_factory=list)


class ReflectionResponse(BaseModel):
    confidence: float
    gaps: list[str]
    recurse: bool
