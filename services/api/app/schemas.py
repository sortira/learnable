from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class WorkspaceRead(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceRead(BaseModel):
    id: str
    workspace_id: str
    kind: str
    title: str
    status: str
    mime_type: str | None
    uri: str | None
    original_filename: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UrlSourceCreate(BaseModel):
    url: AnyHttpUrl
    title: str | None = Field(default=None, max_length=255)


class DocumentRead(BaseModel):
    id: str
    workspace_id: str
    source_id: str
    title: str
    content_markdown: str
    structure_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=8, ge=1, le=25)


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    workspace_id: str
    text: str
    citation: str | None
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class ResearchRunCreate(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


class ResearchRunRead(BaseModel):
    id: str
    workspace_id: str
    query: str
    status: str
    summary: str | None
    report_markdown: str | None
    plan_json: dict[str, Any] = Field(default_factory=dict)
    metrics_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunNodeRead(BaseModel):
    id: str
    research_run_id: str
    node_type: str
    title: str
    status: str
    payload_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceCardRead(BaseModel):
    id: str
    research_run_id: str
    workspace_id: str
    claim: str
    summary: str
    supporting_chunk_ids: list[str]
    citations: list[str]
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchReportRead(BaseModel):
    run: ResearchRunRead
    nodes: list[RunNodeRead]
    evidence_cards: list[EvidenceCardRead]


class FlashcardRead(BaseModel):
    id: str
    concept: str
    front: str
    back: str

    model_config = {"from_attributes": True}


class FlashcardDeckRead(BaseModel):
    id: str
    title: str
    created_at: datetime
    cards: list[FlashcardRead]


class QuizQuestionRead(BaseModel):
    id: str
    concept: str
    prompt: str
    answer: str
    difficulty: str

    model_config = {"from_attributes": True}


class QuizRead(BaseModel):
    id: str
    title: str
    created_at: datetime
    questions: list[QuizQuestionRead]


class QuizAttemptCreate(BaseModel):
    quiz_id: str
    workspace_id: str
    score: float = Field(ge=0.0, le=1.0)
    total_questions: int = Field(ge=1)
    concept_scores: dict[str, float] = Field(default_factory=dict)


class StudyPlanRead(BaseModel):
    id: str
    workspace_id: str
    title: str
    schedule_markdown: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MasteryStateRead(BaseModel):
    concept: str
    mastery_score: float
    attempts_count: int
    updated_at: datetime

    model_config = {"from_attributes": True}
