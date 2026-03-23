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
    startTransition(async () => {
      try {
        await apiFetch(`/api/workspaces/${workspaceId}/learning/${kind}`, {
          method: "POST"
        });
        await refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to generate learning artifact.");
      }
    });
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
                    {quiz.questions.slice(0, 3).map((question) => (
                      <div key={question.id}>
                        <p className="text-sm font-medium">{question.prompt}</p>
                        <p className="mt-2 text-sm text-steel">{question.answer}</p>
                      </div>
                    ))}
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
