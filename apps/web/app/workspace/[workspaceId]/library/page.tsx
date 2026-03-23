import { LibraryClient } from "@/components/workspace/library-client";

type LibraryPageProps = {
  params: Promise<{ workspaceId: string }>;
};

export default async function LibraryPage({ params }: LibraryPageProps) {
  const { workspaceId } = await params;
  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-5xl rounded-[2rem] border border-black/10 bg-white/70 p-8 backdrop-blur">
        <h1 className="text-3xl font-semibold">Source Library</h1>
        <p className="mt-3 text-sm leading-6 text-steel">
          Upload files, fetch URLs, and inspect parsed documents stored in the current workspace.
        </p>
        <div className="mt-8">
          <LibraryClient workspaceId={workspaceId} />
        </div>
      </div>
    </main>
  );
}
