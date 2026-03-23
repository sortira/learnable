from __future__ import annotations

import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.db import Base, engine, get_db
from app import models, schemas
from app.cache import get_cache
from app.retrieval import index_chunks, search_workspace_chunks
from app.research_engine import (
    execute_research_run,
    generate_flashcards_from_run,
    generate_quiz_from_run,
    generate_study_plan_from_run,
    record_quiz_attempt,
)
from app.source_ingestion import ingest_file, ingest_url

settings = get_settings()
cache = get_cache()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Learnable API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/system/health")
def system_health() -> dict[str, str]:
    return {"status": "healthy", "service": "learnable-api"}


@app.post("/api/workspaces", response_model=schemas.WorkspaceRead)
def create_workspace(body: schemas.WorkspaceCreate, db: Session = Depends(get_db)) -> models.Workspace:
    workspace = models.Workspace(name=body.name, description=body.description)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@app.get("/api/workspaces", response_model=list[schemas.WorkspaceRead])
def list_workspaces(db: Session = Depends(get_db)) -> list[models.Workspace]:
    return db.query(models.Workspace).order_by(models.Workspace.created_at.desc()).all()


@app.get("/api/workspaces/{workspace_id}", response_model=schemas.WorkspaceRead)
def get_workspace(workspace_id: str, db: Session = Depends(get_db)) -> models.Workspace:
    workspace = db.get(models.Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@app.post("/api/workspaces/{workspace_id}/sources/upload", response_model=schemas.SourceRead)
def upload_source(
    workspace_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> models.Source:
    workspace = db.get(models.Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    source = models.Source(
        workspace_id=workspace_id,
        kind="upload",
        title=file.filename or "Untitled upload",
        status="processing",
        mime_type=file.content_type,
        original_filename=file.filename,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    destination = settings.object_root / source.id
    destination.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "upload.bin").suffix
    file_path = destination / f"source{suffix}"
    file_bytes = file.file.read()
    if len(file_bytes) > settings.learnable_max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit")
    file_path.write_bytes(file_bytes)

    source.storage_path = str(file_path)
    db.add(source)
    db.commit()

    try:
        parsed = ingest_file(file_path, file.content_type, source.title)
        document = models.Document(
            workspace_id=workspace_id,
            source_id=source.id,
            title=parsed["title"],
            content_markdown=parsed["markdown"],
            structure_json=parsed["structure"],
        )
        db.add(document)
        db.flush()
        chunk_records: list[models.Chunk] = []
        for position, chunk in enumerate(parsed["chunks"]):
            chunk_record = models.Chunk(
                workspace_id=workspace_id,
                document_id=document.id,
                position=position,
                section=chunk["section"],
                text=chunk["text"],
                citation=f"{document.title} • chunk {position + 1}",
                token_count=len(chunk["text"].split()),
                metadata_json={"source_id": source.id},
            )
            db.add(chunk_record)
            chunk_records.append(chunk_record)
        source.status = "ready"
        source.mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0]
    except Exception as exc:
        source.status = "failed"
        source.metadata_json = {"error": str(exc)}
    db.add(source)
    db.commit()
    if source.status == "ready" and "chunk_records" in locals():
        if not index_chunks(chunk_records):
            source.metadata_json = {**(source.metadata_json or {}), "indexing": "vector indexing unavailable; lexical fallback active"}
            db.add(source)
            db.commit()
    cache.delete_prefix(f"search:{workspace_id}:")
    cache.delete_prefix("report:")
    db.refresh(source)
    return source


@app.post("/api/workspaces/{workspace_id}/sources/url", response_model=schemas.SourceRead)
def create_url_source(
    workspace_id: str,
    body: schemas.UrlSourceCreate,
    db: Session = Depends(get_db),
) -> models.Source:
    workspace = db.get(models.Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    source = models.Source(
        workspace_id=workspace_id,
        kind="url",
        title=body.title or str(body.url),
        status="processing",
        uri=str(body.url),
        mime_type="text/html",
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        parsed = ingest_url(str(body.url), body.title)
        document = models.Document(
            workspace_id=workspace_id,
            source_id=source.id,
            title=parsed["title"],
            content_markdown=parsed["markdown"],
            structure_json=parsed["structure"],
        )
        db.add(document)
        db.flush()
        chunk_records: list[models.Chunk] = []
        for position, chunk in enumerate(parsed["chunks"]):
            chunk_record = models.Chunk(
                workspace_id=workspace_id,
                document_id=document.id,
                position=position,
                section=chunk["section"],
                text=chunk["text"],
                citation=f"{document.title} • chunk {position + 1}",
                token_count=len(chunk["text"].split()),
                metadata_json={"source_id": source.id, "url": str(body.url)},
            )
            db.add(chunk_record)
            chunk_records.append(chunk_record)
        source.status = "ready"
        source.title = parsed["title"]
    except Exception as exc:
        source.status = "failed"
        source.metadata_json = {"error": str(exc)}
    db.add(source)
    db.commit()
    if source.status == "ready" and "chunk_records" in locals():
        if not index_chunks(chunk_records):
            source.metadata_json = {**(source.metadata_json or {}), "indexing": "vector indexing unavailable; lexical fallback active"}
            db.add(source)
            db.commit()
    cache.delete_prefix(f"search:{workspace_id}:")
    cache.delete_prefix("report:")
    db.refresh(source)
    return source


@app.get("/api/workspaces/{workspace_id}/sources", response_model=list[schemas.SourceRead])
def list_sources(workspace_id: str, db: Session = Depends(get_db)) -> list[models.Source]:
    return (
        db.query(models.Source)
        .filter(models.Source.workspace_id == workspace_id)
        .order_by(models.Source.created_at.desc())
        .all()
    )


@app.get("/api/workspaces/{workspace_id}/documents", response_model=list[schemas.DocumentRead])
def list_documents(workspace_id: str, db: Session = Depends(get_db)) -> list[models.Document]:
    return (
        db.query(models.Document)
        .filter(models.Document.workspace_id == workspace_id)
        .order_by(models.Document.created_at.desc())
        .all()
    )


@app.post("/api/workspaces/{workspace_id}/search", response_model=schemas.SearchResponse)
def search_workspace(
    workspace_id: str,
    body: schemas.SearchRequest,
    db: Session = Depends(get_db),
) -> schemas.SearchResponse:
    return search_workspace_chunks(db, workspace_id, body)


@app.post("/api/workspaces/{workspace_id}/research-runs", response_model=schemas.ResearchRunRead)
def create_research_run(
    workspace_id: str,
    body: schemas.ResearchRunCreate,
    db: Session = Depends(get_db),
) -> models.ResearchRun:
    workspace = db.get(models.Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    run = models.ResearchRun(workspace_id=workspace_id, query=body.query, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)
    return execute_research_run(db, run)


@app.get("/api/workspaces/{workspace_id}/research-runs", response_model=list[schemas.ResearchRunRead])
def list_research_runs(workspace_id: str, db: Session = Depends(get_db)) -> list[models.ResearchRun]:
    return (
        db.query(models.ResearchRun)
        .filter(models.ResearchRun.workspace_id == workspace_id)
        .order_by(models.ResearchRun.updated_at.desc())
        .all()
    )


@app.get("/api/research-runs/{run_id}", response_model=schemas.ResearchRunRead)
def get_research_run(run_id: str, db: Session = Depends(get_db)) -> models.ResearchRun:
    run = db.get(models.ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/api/research-runs/{run_id}/events", response_model=list[schemas.RunNodeRead])
def get_research_events(run_id: str, db: Session = Depends(get_db)) -> list[models.ResearchRunNode]:
    return (
        db.query(models.ResearchRunNode)
        .filter(models.ResearchRunNode.research_run_id == run_id)
        .order_by(models.ResearchRunNode.created_at.asc())
        .all()
    )


@app.post("/api/research-runs/{run_id}/cancel", response_model=schemas.ResearchRunRead)
def cancel_research_run(run_id: str, db: Session = Depends(get_db)) -> models.ResearchRun:
    run = db.get(models.ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    run.status = "cancelled"
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@app.post("/api/research-runs/{run_id}/retry-node", response_model=schemas.ResearchRunRead)
def retry_research_node(run_id: str, db: Session = Depends(get_db)) -> models.ResearchRun:
    run = db.get(models.ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return execute_research_run(db, run)


@app.get("/api/research-runs/{run_id}/report", response_model=schemas.ResearchReportRead)
def get_report(run_id: str, db: Session = Depends(get_db)) -> schemas.ResearchReportRead:
    run = (
        db.query(models.ResearchRun)
        .options(selectinload(models.ResearchRun.nodes), selectinload(models.ResearchRun.evidence_cards))
        .filter(models.ResearchRun.id == run_id)
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return schemas.ResearchReportRead(
        run=run,
        nodes=run.nodes,
        evidence_cards=run.evidence_cards,
    )


@app.post("/api/workspaces/{workspace_id}/learning/flashcards", response_model=schemas.FlashcardDeckRead)
def create_flashcards(workspace_id: str, db: Session = Depends(get_db)) -> schemas.FlashcardDeckRead:
    run = (
        db.query(models.ResearchRun)
        .options(selectinload(models.ResearchRun.evidence_cards))
        .filter(
            models.ResearchRun.workspace_id == workspace_id,
            models.ResearchRun.status == "completed",
        )
        .order_by(models.ResearchRun.updated_at.desc())
        .first()
    )
    if run is None:
        raise HTTPException(status_code=400, detail="No completed research run available")
    deck = generate_flashcards_from_run(db, run)
    deck = (
        db.query(models.FlashcardDeck)
        .options(selectinload(models.FlashcardDeck.cards))
        .filter(models.FlashcardDeck.id == deck.id)
        .first()
    )
    return deck  # type: ignore[return-value]


@app.get("/api/workspaces/{workspace_id}/learning/flashcards", response_model=list[schemas.FlashcardDeckRead])
def list_flashcard_decks(workspace_id: str, db: Session = Depends(get_db)) -> list[models.FlashcardDeck]:
    return (
        db.query(models.FlashcardDeck)
        .options(selectinload(models.FlashcardDeck.cards))
        .filter(models.FlashcardDeck.workspace_id == workspace_id)
        .order_by(models.FlashcardDeck.created_at.desc())
        .all()
    )


@app.post("/api/workspaces/{workspace_id}/learning/quizzes", response_model=schemas.QuizRead)
def create_quiz(workspace_id: str, db: Session = Depends(get_db)) -> models.Quiz:
    run = (
        db.query(models.ResearchRun)
        .options(selectinload(models.ResearchRun.evidence_cards))
        .filter(
            models.ResearchRun.workspace_id == workspace_id,
            models.ResearchRun.status == "completed",
        )
        .order_by(models.ResearchRun.updated_at.desc())
        .first()
    )
    if run is None:
        raise HTTPException(status_code=400, detail="No completed research run available")
    quiz = generate_quiz_from_run(db, run)
    quiz = (
        db.query(models.Quiz)
        .options(selectinload(models.Quiz.questions))
        .filter(models.Quiz.id == quiz.id)
        .first()
    )
    return quiz  # type: ignore[return-value]


@app.get("/api/workspaces/{workspace_id}/learning/quizzes", response_model=list[schemas.QuizRead])
def list_quizzes(workspace_id: str, db: Session = Depends(get_db)) -> list[models.Quiz]:
    return (
        db.query(models.Quiz)
        .options(selectinload(models.Quiz.questions))
        .filter(models.Quiz.workspace_id == workspace_id)
        .order_by(models.Quiz.created_at.desc())
        .all()
    )


@app.post("/api/workspaces/{workspace_id}/learning/study-plan", response_model=schemas.StudyPlanRead)
def create_study_plan(workspace_id: str, db: Session = Depends(get_db)) -> models.StudyPlan:
    run = (
        db.query(models.ResearchRun)
        .options(selectinload(models.ResearchRun.evidence_cards))
        .filter(
            models.ResearchRun.workspace_id == workspace_id,
            models.ResearchRun.status == "completed",
        )
        .order_by(models.ResearchRun.updated_at.desc())
        .first()
    )
    if run is None:
        raise HTTPException(status_code=400, detail="No completed research run available")
    return generate_study_plan_from_run(db, run)


@app.get("/api/workspaces/{workspace_id}/learning/study-plan", response_model=list[schemas.StudyPlanRead])
def list_study_plans(workspace_id: str, db: Session = Depends(get_db)) -> list[models.StudyPlan]:
    return (
        db.query(models.StudyPlan)
        .filter(models.StudyPlan.workspace_id == workspace_id)
        .order_by(models.StudyPlan.created_at.desc())
        .all()
    )


@app.post("/api/quiz-attempts")
def create_quiz_attempt(body: schemas.QuizAttemptCreate, db: Session = Depends(get_db)) -> dict[str, str]:
    quiz = (
        db.query(models.Quiz)
        .options(selectinload(models.Quiz.questions))
        .filter(models.Quiz.id == body.quiz_id)
        .first()
    )
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    attempt = models.QuizAttempt(
        quiz_id=body.quiz_id,
        workspace_id=body.workspace_id,
        score=body.score,
        total_questions=body.total_questions,
        concept_scores=body.concept_scores,
    )
    record_quiz_attempt(db, attempt, quiz)
    return {"status": "recorded"}


@app.get("/api/workspaces/{workspace_id}/mastery", response_model=list[schemas.MasteryStateRead])
def get_mastery(workspace_id: str, db: Session = Depends(get_db)) -> list[models.MasteryState]:
    return (
        db.query(models.MasteryState)
        .filter(models.MasteryState.workspace_id == workspace_id)
        .order_by(models.MasteryState.updated_at.desc())
        .all()
    )
