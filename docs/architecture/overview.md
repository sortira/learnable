# Learnable Architecture Overview

Learnable uses a local-first service layout:

- `api` owns the product-facing contract
- `ingest` normalizes and parses sources
- `orchestrator` runs autonomous research and learning workflows
- `model-gateway` abstracts local model inference and routing

The prototype optimizes for fast, traceable evidence generation using small local models and aggressive caching.
