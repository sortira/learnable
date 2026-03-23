SHELL := /bin/bash

.PHONY: dev infra api web ingest orchestrator model-gateway lint test

dev:
	@echo "Start infra first, then run the services you need: api, web, ingest, orchestrator, model-gateway."

infra:
	docker compose -f infra/compose/local.yml up -d postgres redis qdrant minio

api:
	cd services/api && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && pnpm dev

ingest:
	cd services/ingest && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8100

orchestrator:
	cd services/orchestrator && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8200

model-gateway:
	cd services/model-gateway && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8300

lint:
	@echo "Lint commands are defined per package."

test:
	cd services/api && python -m pytest
