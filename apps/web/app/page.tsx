import Link from "next/link";
import { WorkspaceList } from "@/components/home/workspace-list";

const sections = [
  {
    title: "Research Workspace",
    body: "Upload papers, ingest links, run autonomous research workflows, and inspect traceable evidence."
  },
  {
    title: "Learning Studio",
    body: "Turn the same corpus into quizzes, flashcards, weak-topic diagnostics, and study plans."
  },
  {
    title: "Local Model Engine",
    body: "Fast sub-1B local models orchestrated through retrieval, reranking, and recursive evidence synthesis."
  }
];

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-10">
        <header className="rounded-[2rem] border border-black/10 bg-white/70 p-8 shadow-[0_20px_50px_rgba(0,0,0,0.08)] backdrop-blur">
          <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div className="max-w-3xl">
              <p className="mb-3 text-sm font-semibold uppercase tracking-[0.3em] text-moss">
                Learnable
              </p>
              <h1 className="text-4xl font-semibold leading-tight md:text-6xl">
                Local-first deep research and study workflows.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-steel md:text-lg">
                Build evidence-grounded reports, semantic search across your corpus, and
                study artifacts from the same knowledge graph.
              </p>
            </div>
            <div className="flex gap-3">
              <Link
                href="#workspaces"
                className="rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition hover:bg-black/85"
              >
                Create a workspace
              </Link>
            </div>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          {sections.map((section) => (
            <article
              key={section.title}
              className="rounded-[1.75rem] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur"
            >
              <h2 className="text-xl font-semibold">{section.title}</h2>
              <p className="mt-3 text-sm leading-6 text-steel">{section.body}</p>
            </article>
          ))}
        </section>

        <WorkspaceList />
      </div>
    </main>
  );
}
