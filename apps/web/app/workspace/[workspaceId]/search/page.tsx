import { SearchClient } from "@/components/workspace/search-client";

type SearchPageProps = {
  params: Promise<{ workspaceId: string }>;
};

export default async function SearchPage({ params }: SearchPageProps) {
  const { workspaceId } = await params;
  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-5xl rounded-[2rem] border border-black/10 bg-white/70 p-8 backdrop-blur">
        <h1 className="text-3xl font-semibold">Semantic Search</h1>
        <p className="mt-3 text-sm leading-6 text-steel">
          Query the workspace corpus and inspect citation-linked evidence blocks.
        </p>
        <div className="mt-8">
          <SearchClient workspaceId={workspaceId} />
        </div>
      </div>
    </main>
  );
}
