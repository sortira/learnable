import { LearnClient } from "@/components/workspace/learn-client";

type LearnPageProps = {
  params: Promise<{ workspaceId: string }>;
};

export default async function LearnPage({ params }: LearnPageProps) {
  const { workspaceId } = await params;
  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-5xl rounded-[2rem] border border-black/10 bg-white/70 p-8 backdrop-blur">
        <h1 className="text-3xl font-semibold">Learning Studio</h1>
        <p className="mt-3 text-sm leading-6 text-steel">
          Generate quizzes, flashcards, study plans, and mastery analytics from the latest grounded report.
        </p>
        <div className="mt-8">
          <LearnClient workspaceId={workspaceId} />
        </div>
      </div>
    </main>
  );
}
