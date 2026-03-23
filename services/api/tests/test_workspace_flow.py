from __future__ import annotations

import io

from fastapi import UploadFile
from starlette.datastructures import Headers
from sqlalchemy.orm import Session

from app import schemas
from app.main import (
    create_flashcards,
    create_quiz,
    create_quiz_attempt,
    create_research_run,
    create_study_plan,
    create_workspace,
    get_mastery,
    get_report,
    list_documents,
    search_workspace,
    upload_source,
)


def test_workspace_ingest_research_and_learning_flow(db: Session) -> None:
    workspace = create_workspace(
        schemas.WorkspaceCreate(
            name="Linear Models",
            description="A workspace for regression fundamentals.",
        ),
        db,
    )
    workspace_id = workspace.id

    upload = UploadFile(
        filename="linear-regression.md",
        file=io.BytesIO(
            (
                "# Linear Regression\n\n"
                "Linear regression estimates relationships between variables.\n\n"
                "## Ordinary Least Squares\n\n"
                "Ordinary least squares minimizes squared residuals and provides a fitted line."
            ).encode("utf-8")
        ),
        headers=Headers({"content-type": "text/markdown"}),
    )
    source = upload_source(workspace_id, upload, db)
    assert source.status == "ready"

    documents = list_documents(workspace_id, db)
    assert len(documents) == 1
    assert documents[0].title == "linear-regression.md"

    search_response = search_workspace(
        workspace_id,
        schemas.SearchRequest(query="ordinary least squares", limit=5),
        db,
    )
    search_results = search_response.results
    assert search_results
    assert "squared residuals" in search_results[0].text.lower()

    run = create_research_run(
        workspace_id,
        schemas.ResearchRunCreate(query="Explain linear regression and what to study next."),
        db,
    )
    assert run.status == "completed"
    assert run.summary

    report = get_report(run.id, db)
    assert report.evidence_cards
    assert report.run.report_markdown
    assert "Research report" in report.run.report_markdown

    flashcards = create_flashcards(workspace_id, db)
    assert flashcards.cards

    quiz = create_quiz(workspace_id, db)
    assert quiz.questions

    study_plan = create_study_plan(workspace_id, db)
    assert "Review the executive summary" in study_plan.schedule_markdown

    first_question = quiz.questions[0]
    attempt_response = create_quiz_attempt(
        schemas.QuizAttemptCreate(
            quiz_id=quiz.id,
            workspace_id=workspace_id,
            score=0.75,
            total_questions=len(quiz.questions),
            concept_scores={first_question.concept: 0.75},
        ),
        db,
    )
    assert attempt_response["status"] == "recorded"

    mastery = get_mastery(workspace_id, db)
    assert mastery
    assert mastery[0].attempts_count >= 1
