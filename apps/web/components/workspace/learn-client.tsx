"use client";

import { useEffect, useState, useTransition } from "react";
import type { FlashcardDeck, MasteryState, Quiz, StudyPlan } from "@/types";
import { apiFetch } from "@/lib/api";

type LearnClientProps = {
  workspaceId: string;
};

export function LearnClient({ workspaceId }: LearnClientProps) {
  const [decks, setDecks] = useState<FlashcardDeck[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [plans, setPlans] = useState<StudyPlan[]>([]);
  const [mastery, setMastery] = useState<MasteryState[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [questionOutcomes, setQuestionOutcomes] = useState<Record<string, "correct" | "incorrect">>({});
  const [submittingQuizId, setSubmittingQuizId] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    void refresh();
  }, [workspaceId]);

  async function refresh() {
    try {
      const [nextDecks, nextQuizzes, nextPlans, nextMastery] = await Promise.all([
        apiFetch<FlashcardDeck[]>(`/api/workspaces/${workspaceId}/learning/flashcards`),
        apiFetch<Quiz[]>(`/api/workspaces/${workspaceId}/learning/quizzes`),
        apiFetch<StudyPlan[]>(`/api/workspaces/${workspaceId}/learning/study-plan`),
        apiFetch<MasteryState[]>(`/api/workspaces/${workspaceId}/mastery`)
      ]);
      setDecks(nextDecks);
      setQuizzes(nextQuizzes);
      setPlans(nextPlans);
      setMastery(nextMastery);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load learning artifacts.");
    }
  }

  function handleGenerate(kind: "flashcards" | "quizzes" | "study-plan") {
    setError(null);
    setStatusMessage(null);
    startTransition(async () => {
      try {
        await apiFetch(`/api/workspaces/${workspaceId}/learning/${kind}`, {
          method: "POST"
        });
        await refresh();
        setStatusMessage(`${labelForArtifact(kind)} generated.`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to generate learning artifact.");
      }
    });
  }

  function setQuestionOutcome(questionId: string, outcome: "correct" | "incorrect") {
    setQuestionOutcomes((current) => ({
      ...current,
      [questionId]: outcome
    }));
  }

  async function submitQuizAttempt(quiz: Quiz) {
    const unanswered = quiz.questions.filter((question) => !questionOutcomes[question.id]);
    if (unanswered.length > 0) {
      setError("Mark each quiz question as correct or incorrect before submitting the attempt.");
      return;
    }

    setError(null);
    setStatusMessage(null);
    setSubmittingQuizId(quiz.id);

    try {
      const correctCount = quiz.questions.filter(
        (question) => questionOutcomes[question.id] === "correct"
      ).length;
      const conceptGroups = new Map<string, number[]>();

      for (const question of quiz.questions) {
        const nextScore = questionOutcomes[question.id] === "correct" ? 1 : 0;
        const scores = conceptGroups.get(question.concept) ?? [];
        scores.push(nextScore);
        conceptGroups.set(question.concept, scores);
      }

      const conceptScores = Object.fromEntries(
        Array.from(conceptGroups.entries()).map(([concept, scores]) => [
          concept,
          scores.reduce((total, score) => total + score, 0) / scores.length
        ])
      );

      await apiFetch("/api/quiz-attempts", {
        method: "POST",
        body: JSON.stringify({
          quiz_id: quiz.id,
          workspace_id: workspaceId,
          score: correctCount / quiz.questions.length,
          total_questions: quiz.questions.length,
          concept_scores: conceptScores
        })
      });
      await refresh();
      setStatusMessage(`Quiz attempt recorded at ${correctCount}/${quiz.questions.length}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record the quiz attempt.");
    } finally {
      setSubmittingQuizId(null);
    }
  }

  function labelForArtifact(kind: "flashcards" | "quizzes" | "study-plan") {
    if (kind === "quizzes") {
      return "Quiz";
    }
    if (kind === "study-plan") {
      return "Study plan";
    }
    return "Flashcards";
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
        <h2 className="text-xl font-semibold">Generate learning artifacts</h2>
        <p className="mt-2 text-sm leading-6 text-steel">
          Learning outputs are generated from the latest grounded research run in this workspace.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            disabled={isPending}
            onClick={() => handleGenerate("flashcards")}
            className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-white"
          >
            Generate flashcards
          </button>
          <button
            type="button"
            disabled={isPending}
            onClick={() => handleGenerate("quizzes")}
            className="rounded-full bg-moss px-5 py-3 text-sm font-medium text-white"
          >
            Generate quiz
          </button>
          <button
            type="button"
            disabled={isPending}
            onClick={() => handleGenerate("study-plan")}
            className="rounded-full bg-ember px-5 py-3 text-sm font-medium text-white"
          >
            Generate study plan
          </button>
        </div>
        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
        {statusMessage ? <p className="mt-2 text-sm text-moss">{statusMessage}</p> : null}
      </section>

      <section className="grid gap-6 xl:grid-cols-3">
        <div className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
          <h2 className="text-xl font-semibold">Flashcards</h2>
          <div className="mt-4 space-y-4">
            {decks.length === 0 ? (
              <p className="text-sm text-steel">No decks generated yet.</p>
            ) : (
              decks.map((deck) => (
                <article key={deck.id} className="rounded-2xl border border-black/10 bg-white/80 p-4">
                  <h3 className="font-medium">{deck.title}</h3>
                  <div className="mt-3 space-y-3">
                    {deck.cards.slice(0, 3).map((card) => (
                      <div key={card.id} className="rounded-2xl bg-sand px-4 py-3">
                        <p className="text-sm font-medium">{card.front}</p>
                        <p className="mt-2 text-sm text-steel">{card.back}</p>
                      </div>
                    ))}
                  </div>
                </article>
              ))
            )}
          </div>
        </div>

        <div className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
          <h2 className="text-xl font-semibold">Quizzes</h2>
          <div className="mt-4 space-y-4">
            {quizzes.length === 0 ? (
              <p className="text-sm text-steel">No quizzes generated yet.</p>
            ) : (
              quizzes.map((quiz) => (
                <article key={quiz.id} className="rounded-2xl border border-black/10 bg-white/80 p-4">
                  <h3 className="font-medium">{quiz.title}</h3>
                  <div className="mt-3 space-y-3">
                    {quiz.questions.map((question) => (
                      <div key={question.id} className="rounded-2xl bg-sand px-4 py-4">
                        <p className="text-sm font-medium">{question.prompt}</p>
                        <p className="mt-2 text-xs uppercase tracking-[0.2em] text-steel">
                          {question.concept} · {question.difficulty}
                        </p>
                        <p className="mt-3 text-sm text-steel">{question.answer}</p>
                        <div className="mt-4 flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() => setQuestionOutcome(question.id, "correct")}
                            className={`rounded-full px-4 py-2 text-xs font-medium transition ${
                              questionOutcomes[question.id] === "correct"
                                ? "bg-moss text-white"
                                : "bg-white text-steel"
                            }`}
                          >
                            I got this right
                          </button>
                          <button
                            type="button"
                            onClick={() => setQuestionOutcome(question.id, "incorrect")}
                            className={`rounded-full px-4 py-2 text-xs font-medium transition ${
                              questionOutcomes[question.id] === "incorrect"
                                ? "bg-ember text-white"
                                : "bg-white text-steel"
                            }`}
                          >
                            I missed this
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex items-center justify-between gap-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-steel">
                      Self-check each answer, then record the attempt to update mastery.
                    </p>
                    <button
                      type="button"
                      disabled={submittingQuizId === quiz.id}
                      onClick={() => void submitQuizAttempt(quiz)}
                      className="rounded-full bg-ink px-4 py-2 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {submittingQuizId === quiz.id ? "Saving..." : "Record attempt"}
                    </button>
                  </div>
                </article>
              ))
            )}
          </div>
        </div>

        <div className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
          <h2 className="text-xl font-semibold">Study plans & mastery</h2>
          <div className="mt-4 space-y-4">
            {plans.length === 0 ? (
              <p className="text-sm text-steel">No study plans generated yet.</p>
            ) : (
              plans.map((plan) => (
                <article key={plan.id} className="rounded-2xl border border-black/10 bg-white/80 p-4">
                  <h3 className="font-medium">{plan.title}</h3>
                  <pre className="mt-3 whitespace-pre-wrap text-sm leading-6 text-steel">
                    {plan.schedule_markdown}
                  </pre>
                </article>
              ))
            )}
            <div className="rounded-2xl border border-dashed border-black/15 bg-white/50 p-4">
              <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-steel">Mastery</h3>
              <div className="mt-3 space-y-2">
                {mastery.length === 0 ? (
                  <p className="text-sm text-steel">No mastery data yet.</p>
                ) : (
                  mastery.map((state) => (
                    <div key={state.concept} className="flex items-center justify-between gap-4 text-sm">
                      <span>{state.concept}</span>
                      <span className="text-moss">{(state.mastery_score * 100).toFixed(0)}%</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
