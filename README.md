# Learnable

Learnable is a local-first AI research and learning system built for fast, evidence-grounded knowledge work.

## Product

Learnable combines two first-class workflows:

- Research Workspace: ingest documents and links, run autonomous deep-research workflows, and generate traceable reports.
- Learning Studio: turn the same corpus into quizzes, flashcards, concept notes, study plans, and progress analytics.

## Prototype architecture

- `apps/web`: Next.js web app
- `services/api`: FastAPI control plane
- `services/ingest`: ingestion worker service
- `services/orchestrator`: autonomous research workflow service
- `services/model-gateway`: local-model adapter and routing layer
- `packages/contracts`: shared TypeScript contracts
- `infra/compose`: local infrastructure stack

## Current implementation

The repo is a clean rebuild. The current baseline already includes:

- workspace creation and listing
- source ingestion for local text/markdown uploads
- URL ingestion with HTML extraction
- structure-aware document chunking
- lexical grounded search across workspace chunks
- bounded research runs that create evidence cards and markdown reports
- learning artifact generation:
  - flashcards
  - quizzes
  - study plans
  - mastery updates from quiz attempts
- dedicated support services with explicit contracts:
  - `ingest`: text parsing and chunking
  - `orchestrator`: plan and reflection endpoints
  - `model-gateway`: role-based local model routing with `mock` and Ollama modes

The current research engine is intentionally heuristic-first so the prototype is runnable without requiring local models to be installed on day one. The service boundaries and model gateway are already in place for the next integration pass.

## Local stack

- PostgreSQL
- Redis
- Qdrant
- MinIO
- Ollama
- Docling (optional parser extra)

## Model strategy

The prototype is intentionally constrained to local models at `<=1B` parameters. It relies on:

- `Qwen3-0.6B` for planning and routing
- `Gemma-3-1B-IT` or `Llama-3.2-1B-Instruct` for synthesis
- `Qwen3-Embedding-0.6B` for embeddings
- `bge-reranker-v2-m3` for reranking

## Quick start

1. Copy `.env.example` to `.env`
2. Start infra:

```bash
make infra
```

3. Start the API and web app in separate terminals:

```bash
make api
make web
```

4. Optional support services:

```bash
make ingest
make orchestrator
make model-gateway
```

5. Optional richer document parsing:

```bash
cd services/api
uv pip install ".[parsers]"
```

## Local model mode

`services/model-gateway` supports two operating modes:

- `mock`: default, deterministic local fallback for early development
- `ollama`: forwards generation and embedding requests to a local Ollama instance

Set `LEARNABLE_MODEL_GATEWAY_MODE=ollama` when the required local models are installed.

## Status

This repository has been fully reset and rebuilt from scratch. No legacy application code or git history is retained from the previous prototype.
