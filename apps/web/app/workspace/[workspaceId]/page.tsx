import Link from "next/link";
import { notFound } from "next/navigation";

import { apiFetch } from "@/lib/api";
import type { Workspace } from "@/types";

type WorkspacePageProps = {
  params: Promise<{ workspaceId: string }>;
};

const cards = [
  {
    title: "Library",
    description: "Track uploaded sources, parsing progress, and chunked documents.",
    href: "library"
  },
  {
    title: "Search",
    description: "Query the corpus with hybrid and semantic retrieval.",
    href: "search"
  },
  {
    title: "Research",
    description: "Launch a deep research run and inspect evidence cards.",
    href: "research"
  },
  {
    title: "Learning",
    description: "Generate quizzes, flashcards, and schedules from the same corpus.",
    href: "learn"
  }
];

export default async function WorkspacePage({ params }: WorkspacePageProps) {
  const { workspaceId } = await params;
  let workspace: Workspace;

  try {
    workspace = await apiFetch<Workspace>(`/api/workspaces/${workspaceId}`);
  } catch {
    notFound();
  }

  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="rounded-[2rem] border border-black/10 bg-white/70 p-8 backdrop-blur">
          <p className="text-sm uppercase tracking-[0.3em] text-moss">Workspace</p>
          <h1 className="mt-3 text-4xl font-semibold">{workspace.name}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-steel">
            {workspace.description ??
              "Source ingestion, grounded research runs, and learning artifacts all live inside the same workspace."}
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-2">
          {cards.map((card) => (
            <Link
              key={card.title}
              href={`/workspace/${workspaceId}/${card.href}`}
              className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 transition hover:border-black/20 hover:bg-white/80"
            >
              <h2 className="text-xl font-semibold">{card.title}</h2>
              <p className="mt-3 text-sm leading-6 text-steel">{card.description}</p>
            </Link>
          ))}
        </section>
      </div>
    </main>
  );
}
