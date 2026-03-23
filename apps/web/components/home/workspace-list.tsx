"use client";

import Link from "next/link";
import { useEffect, useState, useTransition } from "react";
import type { Workspace } from "@learnable/contracts";
import { apiFetch } from "@/lib/api";

export function WorkspaceList() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    void loadWorkspaces();
  }, []);

  async function loadWorkspaces() {
    try {
      const data = await apiFetch<Workspace[]>("/api/workspaces");
      setWorkspaces(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workspaces.");
    }
  }

  function handleCreateWorkspace(formData: FormData) {
    const nextName = String(formData.get("name") ?? "").trim();
    const nextDescription = String(formData.get("description") ?? "").trim();
    if (!nextName) {
      setError("Workspace name is required.");
      return;
    }
    setError(null);
    startTransition(async () => {
      try {
        const workspace = await apiFetch<Workspace>("/api/workspaces", {
          method: "POST",
          body: JSON.stringify({
            name: nextName,
            description: nextDescription || null
          })
        });
        setWorkspaces((current) => [workspace, ...current]);
        setName("");
        setDescription("");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create workspace.");
      }
    });
  }

  return (
    <section id="workspaces" className="grid gap-6 md:grid-cols-[1.2fr_0.8fr]">
      <div className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 backdrop-blur">
        <h2 className="text-xl font-semibold">Workspaces</h2>
        <p className="mt-2 text-sm leading-6 text-steel">
          Each workspace is a knowledge container for sources, reports, and learning artifacts.
        </p>
        <div className="mt-6 space-y-3">
          {workspaces.length === 0 ? (
            <p className="rounded-2xl border border-dashed border-black/15 px-4 py-6 text-sm text-steel">
              No workspaces yet. Create one to start ingesting sources.
            </p>
          ) : (
            workspaces.map((workspace) => (
              <Link
                key={workspace.id}
                href={`/workspace/${workspace.id}`}
                className="block rounded-2xl border border-black/10 bg-white/80 px-4 py-4 transition hover:border-black/20"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-medium">{workspace.name}</h3>
                    <p className="mt-1 text-sm text-steel">
                      {workspace.description ?? "No description provided."}
                    </p>
                  </div>
                  <span className="rounded-full bg-sand px-3 py-1 text-xs uppercase tracking-[0.2em] text-moss">
                    Open
                  </span>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>

      <div className="rounded-[1.75rem] border border-black/10 bg-ink p-6 text-white">
        <h2 className="text-xl font-semibold">Create a workspace</h2>
        <p className="mt-2 text-sm leading-6 text-white/70">
          Start with a focused corpus for a topic, project, class, or research sprint.
        </p>
        <form action={handleCreateWorkspace} className="mt-6 space-y-4">
          <label className="block">
            <span className="mb-2 block text-sm text-white/80">Name</span>
            <input
              name="name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="w-full rounded-2xl border border-white/15 bg-white/5 px-4 py-3 text-sm outline-none transition focus:border-white/30"
              placeholder="Machine Learning Papers"
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm text-white/80">Description</span>
            <textarea
              name="description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="min-h-28 w-full rounded-2xl border border-white/15 bg-white/5 px-4 py-3 text-sm outline-none transition focus:border-white/30"
              placeholder="A workspace for evidence-grounded research and study artifacts."
            />
          </label>
          {error ? <p className="text-sm text-red-300">{error}</p> : null}
          <button
            type="submit"
            disabled={isPending}
            className="rounded-full bg-white px-5 py-3 text-sm font-medium text-ink transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isPending ? "Creating..." : "Create workspace"}
          </button>
        </form>
      </div>
    </section>
  );
}
