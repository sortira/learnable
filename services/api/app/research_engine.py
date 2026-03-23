from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app import models
from app.cache import get_cache
from app.retrieval import lexical_score, retrieve_chunks_for_query
from app.service_clients import create_plan, generate_text, reflect_on_evidence

cache = get_cache()


def derive_sub_questions(query: str) -> list[str]:
    query = query.strip().rstrip("?")
    base = re.sub(r"\s+", " ", query)
    return [
        f"What are the core ideas behind {base}?",
        f"What evidence or sources best explain {base}?",
        f"What should someone study next to understand {base} deeply?",
    ]


def summarize_chunk_text(text: str, max_sentences: int = 2) -> str:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    if not sentences:
        return text[:240]
    return " ".join(sentences[:max_sentences])[:500]


def build_report(query: str, chunks: list[models.Chunk]) -> tuple[str, str]:
    if not chunks:
        empty = (
            f"# Research report\n\n"
            f"## Query\n\n{query}\n\n"
            "No relevant evidence was found in the current workspace corpus. Add more sources and run the report again."
        )
        return "No evidence found for the requested topic.", empty

    summary = f"Found {len(chunks)} grounded evidence blocks relevant to '{query}'."

    bullets = []
    for chunk in chunks:
        citation = chunk.citation or "Unknown source"
        bullets.append(f"- **{citation}**: {summarize_chunk_text(chunk.text)}")

    concepts = [chunk.section for chunk in chunks if chunk.section]
    next_steps = "\n".join(f"- Review {concept}" for concept in concepts[:3]) or "- Review the core evidence sources"
    markdown = (
        "# Research report\n\n"
        f"## Query\n\n{query}\n\n"
        f"## Executive summary\n\n{summary}\n\n"
        "## Evidence highlights\n\n"
        f"{chr(10).join(bullets)}\n\n"
        "## Study implications\n\n"
        "The current evidence can be converted into targeted quizzes, flashcards, and a study plan.\n\n"
        "## Suggested next steps\n\n"
        f"{next_steps}\n"
    )
    return summary, markdown


def synthesize_report(query: str, chunks: list[models.Chunk], fallback_markdown: str) -> tuple[str, str]:
    if not chunks:
        return "No evidence found for the requested topic.", fallback_markdown

    cache_key = f"report:{query}:{','.join(chunk.id for chunk in chunks)}"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return cached["summary"], cached["markdown"]

    evidence_lines = [
        f"- {chunk.citation or 'Unknown source'}: {summarize_chunk_text(chunk.text)}"
        for chunk in chunks[:6]
    ]
    response = generate_text(
        "synthesize",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are producing a concise evidence-grounded research note. "
                    "Do not invent sources. Keep the output tight and actionable."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Query: {query}\n\n"
                    "Evidence:\n"
                    f"{chr(10).join(evidence_lines)}\n\n"
                    "Write a grounded summary and next steps."
                ),
            },
        ],
        max_tokens=500,
    )
    if response is None or not response.get("output_text"):
        return build_report(query, chunks)

    summary = f"Found {len(chunks)} grounded evidence blocks relevant to '{query}'."
    markdown = (
        "# Research report\n\n"
        f"## Query\n\n{query}\n\n"
        "## Executive summary\n\n"
        f"{response['output_text'].strip()}\n\n"
        "## Evidence highlights\n\n"
        f"{chr(10).join(evidence_lines)}\n"
    )
    cache.set_json(cache_key, {"summary": summary, "markdown": markdown})
    return summary, markdown


def build_evidence_cards(run: models.ResearchRun, chunks: list[models.Chunk]) -> list[models.EvidenceCard]:
    cards: list[models.EvidenceCard] = []
    for index, chunk in enumerate(chunks):
        cards.append(
            models.EvidenceCard(
                research_run_id=run.id,
                workspace_id=run.workspace_id,
                claim=summarize_chunk_text(chunk.text, max_sentences=1),
                summary=summarize_chunk_text(chunk.text, max_sentences=2),
                supporting_chunk_ids=[chunk.id],
                citations=[chunk.citation or f"Chunk {index + 1}"],
                confidence=max(0.45, min(0.95, lexical_score(run.query, chunk.text) * 40)),
            )
        )
    return cards


def execute_research_run(db: Session, run: models.ResearchRun) -> models.ResearchRun:
    db.query(models.ResearchRunNode).filter(models.ResearchRunNode.research_run_id == run.id).delete()
    db.query(models.EvidenceCard).filter(models.EvidenceCard.research_run_id == run.id).delete()

    run.status = "running"
    run.plan_json = create_plan(run.query) or {
        "objective": run.query,
        "sub_questions": derive_sub_questions(run.query),
    }
    db.add(
        models.ResearchRunNode(
            research_run_id=run.id,
            node_type="planner",
            title="Generated bounded research plan",
            payload_json=run.plan_json,
        )
    )

    selected_results = retrieve_chunks_for_query(db, run.workspace_id, run.query)
    selected_chunks = [chunk for chunk, _score in selected_results]
    db.add(
        models.ResearchRunNode(
            research_run_id=run.id,
            node_type="retrieval",
            title="Selected supporting evidence blocks",
            payload_json={"chunk_ids": [chunk.id for chunk in selected_chunks]},
        )
    )

    evidence_cards = build_evidence_cards(run, selected_chunks)
    for card in evidence_cards:
        db.add(card)

    reflection = reflect_on_evidence(run.query, [card.summary for card in evidence_cards])
    if reflection is not None:
        db.add(
            models.ResearchRunNode(
                research_run_id=run.id,
                node_type="reflection",
                title="Reflected on evidence coverage",
                payload_json=reflection,
            )
        )

    _fallback_summary, fallback_markdown = build_report(run.query, selected_chunks)
    summary, markdown = synthesize_report(run.query, selected_chunks, fallback_markdown)
    run.summary = summary
    run.report_markdown = markdown
    run.status = "completed"
    run.metrics_json = {
        "evidence_count": len(evidence_cards),
        "selected_chunk_count": len(selected_chunks),
        "reflection": reflection or {},
    }
    db.add(
        models.ResearchRunNode(
            research_run_id=run.id,
            node_type="synthesis",
            title="Synthesized grounded report",
            payload_json={"summary": summary},
        )
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def generate_flashcards_from_run(db: Session, run: models.ResearchRun) -> models.FlashcardDeck:
    deck = models.FlashcardDeck(
        research_run_id=run.id,
        workspace_id=run.workspace_id,
        title=f"Flashcards for {run.query[:60]}",
    )
    db.add(deck)
    db.flush()

    for card in run.evidence_cards[:8]:
        concept = card.citations[0] if card.citations else "Core concept"
        db.add(
            models.Flashcard(
                deck_id=deck.id,
                concept=concept,
                front=f"What does the evidence say about {concept}?",
                back=card.summary,
            )
        )

    db.commit()
    db.refresh(deck)
    return deck


def generate_quiz_from_run(db: Session, run: models.ResearchRun) -> models.Quiz:
    quiz = models.Quiz(
        research_run_id=run.id,
        workspace_id=run.workspace_id,
        title=f"Quiz for {run.query[:60]}",
    )
    db.add(quiz)
    db.flush()

    for card in run.evidence_cards[:6]:
        concept = card.citations[0] if card.citations else "Core concept"
        db.add(
            models.QuizQuestion(
                quiz_id=quiz.id,
                concept=concept,
                prompt=f"Explain the main takeaway from {concept}.",
                answer=card.summary,
                difficulty="medium",
            )
        )

    db.commit()
    db.refresh(quiz)
    return quiz


def generate_study_plan_from_run(db: Session, run: models.ResearchRun) -> models.StudyPlan:
    concepts = [card.citations[0] for card in run.evidence_cards[:4] if card.citations]
    steps = [
        "1. Review the executive summary and mark unfamiliar terms.",
        "2. Read the linked evidence blocks in the source library.",
        "3. Complete the generated quiz and review missed concepts.",
        "4. Revisit the flashcards for spaced repetition.",
    ]
    if concepts:
        steps.insert(2, "3. Focus on these concept anchors: " + ", ".join(concepts))

    plan = models.StudyPlan(
        research_run_id=run.id,
        workspace_id=run.workspace_id,
        title=f"Study plan for {run.query[:60]}",
        schedule_markdown="\n".join(steps),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def record_quiz_attempt(db: Session, attempt: models.QuizAttempt, quiz: models.Quiz) -> None:
    db.add(attempt)

    for question in quiz.questions:
        concept_score = attempt.concept_scores.get(question.concept, attempt.score)
        state = (
            db.query(models.MasteryState)
            .filter(
                models.MasteryState.workspace_id == attempt.workspace_id,
                models.MasteryState.concept == question.concept,
            )
            .first()
        )
        if state is None:
            state = models.MasteryState(
                workspace_id=attempt.workspace_id,
                concept=question.concept,
                mastery_score=concept_score,
                attempts_count=1,
            )
        else:
            state.mastery_score = round((state.mastery_score * state.attempts_count + concept_score) / (state.attempts_count + 1), 4)
            state.attempts_count += 1
        db.add(state)
    db.commit()
