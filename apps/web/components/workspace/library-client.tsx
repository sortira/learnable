"use client";

import { useEffect, useState, useTransition } from "react";
import type { Document, Source } from "@/types";
import { apiFetch } from "@/lib/api";

type LibraryClientProps = {
  workspaceId: string;
};

export function LibraryClient({ workspaceId }: LibraryClientProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    void refresh();
  }, [workspaceId]);

  async function refresh() {
    try {
      const [nextSources, nextDocuments] = await Promise.all([
        apiFetch<Source[]>(`/api/workspaces/${workspaceId}/sources`),
        apiFetch<Document[]>(`/api/workspaces/${workspaceId}/documents`)
      ]);
      setSources(nextSources);
      setDocuments(nextDocuments);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load library.");
    }
  }

  function handleUrlSubmit(formData: FormData) {
    const nextUrl = String(formData.get("url") ?? "").trim();
    if (!nextUrl) {
      return;
    }
    setError(null);
    startTransition(async () => {
      try {
        await apiFetch(`/api/workspaces/${workspaceId}/sources/url`, {
          method: "POST",
          body: JSON.stringify({ url: nextUrl })
        });
        setUrl("");
        await refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to add URL source.");
      }
    });
  }

  function handleUpload(formData: FormData) {
    const file = formData.get("file");
    if (!(file instanceof File)) {
      setError("Choose a file to upload.");
      return;
    }
    setError(null);
    startTransition(async () => {
      try {
        const payload = new FormData();
        payload.set("file", file);
        await apiFetch(`/api/workspaces/${workspaceId}/sources/upload`, {
          method: "POST",
          body: payload
        });
        await refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to upload source.");
      }
    });
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <section className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
        <h2 className="text-xl font-semibold">Ingest sources</h2>
        <p className="mt-2 text-sm leading-6 text-steel">
          Add papers, notes, and links to seed the research and learning engine.
        </p>
        <div className="mt-6 space-y-6">
          <form action={handleUpload} className="space-y-3">
            <label className="block text-sm font-medium">Upload a file</label>
            <input
              name="file"
              type="file"
              className="block w-full rounded-2xl border border-black/10 bg-sand px-4 py-3 text-sm"
            />
            <button
              type="submit"
              disabled={isPending}
              className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-white"
            >
              {isPending ? "Uploading..." : "Upload"}
            </button>
          </form>

          <form action={handleUrlSubmit} className="space-y-3">
            <label className="block text-sm font-medium">Add a URL</label>
            <input
              name="url"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              className="w-full rounded-2xl border border-black/10 bg-sand px-4 py-3 text-sm outline-none"
              placeholder="https://example.com/research-paper"
            />
            <button
              type="submit"
              disabled={isPending}
              className="rounded-full bg-moss px-5 py-3 text-sm font-medium text-white"
            >
              {isPending ? "Fetching..." : "Fetch URL"}
            </button>
          </form>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
        </div>
      </section>

      <section className="space-y-6">
        <div className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
          <h2 className="text-xl font-semibold">Sources</h2>
          <div className="mt-4 space-y-3">
            {sources.length === 0 ? (
              <p className="text-sm text-steel">No sources yet.</p>
            ) : (
              sources.map((source) => (
                <div key={source.id} className="rounded-2xl border border-black/10 bg-white/80 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-medium">{source.title}</h3>
                      <p className="mt-1 text-xs uppercase tracking-[0.2em] text-steel">
                        {source.kind} · {source.status}
                      </p>
                    </div>
                    <span className="rounded-full bg-sand px-3 py-1 text-xs text-moss">
                      {source.mime_type ?? "Unknown"}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
          <h2 className="text-xl font-semibold">Parsed documents</h2>
          <div className="mt-4 space-y-4">
            {documents.length === 0 ? (
              <p className="text-sm text-steel">No parsed documents yet.</p>
            ) : (
              documents.map((document) => (
                <article key={document.id} className="rounded-2xl border border-black/10 bg-white/80 p-4">
                  <h3 className="font-medium">{document.title}</h3>
                  <p className="mt-2 line-clamp-4 text-sm leading-6 text-steel">
                    {document.content_markdown}
                  </p>
                </article>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
