"use client";

import { type FormEvent, useState, useTransition } from "react";
import type { SearchResponse } from "@/types";
import { apiFetch } from "@/lib/api";

type SearchClientProps = {
  workspaceId: string;
};

export function SearchClient({ workspaceId }: SearchClientProps) {
  const [query, setQuery] = useState("");
  const [data, setData] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextQuery = query.trim();
    if (!nextQuery) {
      setError("A search query is required.");
      return;
    }
    setError(null);
    startTransition(async () => {
      try {
        const response = await apiFetch<SearchResponse>(`/api/workspaces/${workspaceId}/search`, {
          method: "POST",
          body: JSON.stringify({ query: nextQuery, limit: 10 })
        });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed.");
      }
    });
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
        <h2 className="text-xl font-semibold">Search the workspace</h2>
        <p className="mt-2 text-sm leading-6 text-steel">
          Query the current corpus and inspect chunk-level grounded results.
        </p>
        <form onSubmit={handleSearch} className="mt-6 flex flex-col gap-3 md:flex-row">
          <input
            name="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            required
            className="flex-1 rounded-full border border-black/10 bg-sand px-5 py-3 text-sm outline-none"
            placeholder="Search for a concept, method, or claim"
          />
          <button
            type="submit"
            disabled={isPending}
            className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-white"
          >
            {isPending ? "Searching..." : "Search"}
          </button>
        </form>
        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      </section>

      <section className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
        <h2 className="text-xl font-semibold">Results</h2>
        <div className="mt-4 space-y-4">
          {!data ? (
            <p className="text-sm text-steel">Run a query to inspect chunk-level results.</p>
          ) : data.results.length === 0 ? (
            <p className="text-sm text-steel">No results found.</p>
          ) : (
            data.results.map((result) => (
              <article key={result.chunk_id} className="rounded-2xl border border-black/10 bg-white/80 p-4">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-xs uppercase tracking-[0.2em] text-steel">
                    {result.citation ?? "No citation"}
                  </span>
                  <span className="rounded-full bg-sand px-3 py-1 text-xs text-moss">
                    Score {result.score.toFixed(3)}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-steel">{result.text}</p>
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
