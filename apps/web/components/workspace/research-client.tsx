"use client";

import { useEffect, useState, useTransition } from "react";
import type { Report, ResearchRun } from "@/types";
import { apiFetch } from "@/lib/api";

type ResearchClientProps = {
  workspaceId: string;
};

export function ResearchClient({ workspaceId }: ResearchClientProps) {
  const [query, setQuery] = useState("");
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    void loadRuns();
  }, [workspaceId]);

  async function loadRuns() {
    try {
      const data = await apiFetch<ResearchRun[]>(`/api/workspaces/${workspaceId}/research-runs`);
      setRuns(data);
      if (data[0]) {
        const report = await apiFetch<Report>(`/api/research-runs/${data[0].id}/report`);
        setSelectedReport(report);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load runs.");
    }
  }

  function handleRun(formData: FormData) {
    const nextQuery = String(formData.get("query") ?? "").trim();
    if (!nextQuery) {
      return;
    }
    setError(null);
    startTransition(async () => {
      try {
        const run = await apiFetch<ResearchRun>(`/api/workspaces/${workspaceId}/research-runs`, {
          method: "POST",
          body: JSON.stringify({ query: nextQuery })
        });
        const report = await apiFetch<Report>(`/api/research-runs/${run.id}/report`);
        setRuns((current) => [run, ...current]);
        setSelectedReport(report);
        setQuery("");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to execute research run.");
      }
    });
  }

  async function selectRun(runId: string) {
    try {
      const report = await apiFetch<Report>(`/api/research-runs/${runId}/report`);
      setSelectedReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load report.");
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
      <section className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
        <h2 className="text-xl font-semibold">Launch a research run</h2>
        <p className="mt-2 text-sm leading-6 text-steel">
          The current backend executes a bounded, evidence-grounded research workflow over the workspace corpus.
        </p>
        <form action={handleRun} className="mt-6 space-y-3">
          <textarea
            name="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="min-h-32 w-full rounded-[1.5rem] border border-black/10 bg-sand px-5 py-4 text-sm outline-none"
            placeholder="Compare the central ideas across these sources and tell me what to study next."
          />
          <button
            type="submit"
            disabled={isPending}
            className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-white"
          >
            {isPending ? "Running..." : "Run deep research"}
          </button>
        </form>
        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

        <div className="mt-8 space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-steel">Recent runs</h3>
          {runs.length === 0 ? (
            <p className="text-sm text-steel">No research runs yet.</p>
          ) : (
            runs.map((run) => (
              <button
                key={run.id}
                type="button"
                onClick={() => void selectRun(run.id)}
                className="block w-full rounded-2xl border border-black/10 bg-white/80 px-4 py-4 text-left transition hover:border-black/20"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h4 className="font-medium">{run.query}</h4>
                    <p className="mt-1 text-sm text-steel">{run.summary ?? "Completed run"}</p>
                  </div>
                  <span className="rounded-full bg-sand px-3 py-1 text-xs uppercase tracking-[0.2em] text-moss">
                    {run.status}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </section>

      <section className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
        <h2 className="text-xl font-semibold">Latest report</h2>
        {!selectedReport ? (
          <p className="mt-4 text-sm text-steel">Run a grounded research job to generate a report.</p>
        ) : (
          <div className="mt-4 space-y-6">
            <article className="rounded-2xl border border-black/10 bg-white/80 p-5">
              <h3 className="font-medium">{selectedReport.run.query}</h3>
              <pre className="mt-4 whitespace-pre-wrap text-sm leading-6 text-steel">
                {selectedReport.run.report_markdown ?? "No report available."}
              </pre>
            </article>
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-steel">Evidence cards</h3>
              <div className="mt-3 space-y-3">
                {selectedReport.evidence_cards.map((card) => (
                  <article key={card.id} className="rounded-2xl border border-black/10 bg-white/80 p-4">
                    <h4 className="font-medium">{card.claim}</h4>
                    <p className="mt-2 text-sm leading-6 text-steel">{card.summary}</p>
                    <p className="mt-3 text-xs uppercase tracking-[0.2em] text-moss">
                      {card.citations.join(" · ")}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
