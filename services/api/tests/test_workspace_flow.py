from __future__ import annotations

from fastapi.testclient import TestClient


def test_workspace_ingest_research_and_learning_flow(client: TestClient) -> None:
    workspace_response = client.post(
        "/api/workspaces",
        json={
            "name": "Linear Models",
            "description": "A workspace for regression fundamentals.",
        },
    )
    assert workspace_response.status_code == 200
    workspace = workspace_response.json()
    workspace_id = workspace["id"]

    upload_response = client.post(
        f"/api/workspaces/{workspace_id}/sources/upload",
        files={
            "file": (
                "linear-regression.md",
                (
                    "# Linear Regression\n\n"
                    "Linear regression estimates relationships between variables.\n\n"
                    "## Ordinary Least Squares\n\n"
                    "Ordinary least squares minimizes squared residuals and provides a fitted line."
                ),
                "text/markdown",
            )
        },
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["status"] == "ready"

    documents_response = client.get(f"/api/workspaces/{workspace_id}/documents")
    assert documents_response.status_code == 200
    documents = documents_response.json()
    assert len(documents) == 1
    assert documents[0]["title"] == "linear-regression.md"

    search_response = client.post(
        f"/api/workspaces/{workspace_id}/search",
        json={"query": "ordinary least squares", "limit": 5},
    )
    assert search_response.status_code == 200
    search_results = search_response.json()["results"]
    assert search_results
    assert "squared residuals" in search_results[0]["text"].lower()

    run_response = client.post(
        f"/api/workspaces/{workspace_id}/research-runs",
        json={"query": "Explain linear regression and what to study next."},
    )
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["status"] == "completed"
    assert run["summary"]

    report_response = client.get(f"/api/research-runs/{run['id']}/report")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["evidence_cards"]
    assert "Research report" in report["run"]["report_markdown"]

    flashcards_response = client.post(f"/api/workspaces/{workspace_id}/learning/flashcards")
    assert flashcards_response.status_code == 200
    flashcards = flashcards_response.json()
    assert flashcards["cards"]

    quiz_response = client.post(f"/api/workspaces/{workspace_id}/learning/quizzes")
    assert quiz_response.status_code == 200
    quiz = quiz_response.json()
    assert quiz["questions"]

    study_plan_response = client.post(f"/api/workspaces/{workspace_id}/learning/study-plan")
    assert study_plan_response.status_code == 200
    study_plan = study_plan_response.json()
    assert "Review the executive summary" in study_plan["schedule_markdown"]

    first_question = quiz["questions"][0]
    attempt_response = client.post(
        "/api/quiz-attempts",
        json={
            "quiz_id": quiz["id"],
            "workspace_id": workspace_id,
            "score": 0.75,
            "total_questions": len(quiz["questions"]),
            "concept_scores": {
                first_question["concept"]: 0.75,
            },
        },
    )
    assert attempt_response.status_code == 200
    assert attempt_response.json()["status"] == "recorded"

    mastery_response = client.get(f"/api/workspaces/{workspace_id}/mastery")
    assert mastery_response.status_code == 200
    mastery = mastery_response.json()
    assert mastery
    assert mastery[0]["attempts_count"] >= 1
