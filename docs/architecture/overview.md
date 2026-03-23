# Learnable Architecture Overview

Learnable is organized as a local-first monorepo with a thin product-facing API and explicit service boundaries for parsing, orchestration, and model access.

## Core services

- `apps/web`
  - Next.js application
  - owns the end-user interface
- `services/api`
  - FastAPI control plane
  - owns the product contract and persistence flow
- `services/ingest`
  - parsing and normalization boundary
- `services/orchestrator`
  - planning and reflection boundary
- `services/model-gateway`
  - local model routing boundary

## Product pipeline

1. sources enter a workspace
2. sources are normalized into markdown
3. markdown is chunked into evidence-ready units
4. chunks are stored and optionally indexed
5. search and research runs retrieve relevant chunks
6. reports and evidence cards are generated
7. learning artifacts are derived from the latest grounded run

## Storage strategy

- SQLite by default for easy local startup
- Postgres for fuller local infrastructure mode
- filesystem-backed object storage by default
- optional Qdrant vector storage
- optional Redis cache layer

## Model strategy

The prototype is designed around small local models capped at `<=1B` parameters:

- planner: `qwen3:0.6b`
- synthesizer: `gemma3:1b`
- synthesizer fallback: `llama3.2:1b`
- embeddings: `qwen3-embedding:0.6b`

The model gateway currently supports:

- `mock` mode for deterministic development
- `ollama` mode for local inference

## Current implementation posture

The architecture is intentionally ahead of the implementation. The repo shape is production-oriented, while some runtime behaviors still use conservative fallback logic so the app remains easy to run on a laptop.
