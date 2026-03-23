import { ResearchClient } from "@/components/workspace/research-client";

type ResearchPageProps = {
  params: Promise<{ workspaceId: string }>;
};

export default async function ResearchPage({ params }: ResearchPageProps) {
  const { workspaceId } = await params;
  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-5xl rounded-[2rem] border border-black/10 bg-white/70 p-8 backdrop-blur">
        <h1 className="text-3xl font-semibold">Deep Research Runs</h1>
        <p className="mt-3 text-sm leading-6 text-steel">
          Launch a grounded research run across the workspace corpus and inspect the generated evidence cards.
        </p>
        <div className="mt-8">
          <ResearchClient workspaceId={workspaceId} />
        </div>
      </div>
    </main>
  );
}
