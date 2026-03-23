# Local Development

## Recommended path

For day-to-day development, use the minimal local run first:

- SQLite
- local filesystem storage
- mock model gateway
- no Docker required

## Services

- Web: `apps/web`
- API: `services/api`
- Ingest: `services/ingest`
- Orchestrator: `services/orchestrator`
- Model gateway: `services/model-gateway`
- Infra: `infra/compose/local.yml`

## Setup

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e services/api[dev] -e services/ingest -e services/orchestrator -e services/model-gateway
corepack enable
corepack pnpm install
cp .env.example .env
```

## Start commands

```bash
source .venv/bin/activate
cd services/model-gateway
python -m uvicorn app.main:app --host 127.0.0.1 --port 8300
```

```bash
source .venv/bin/activate
cd services/orchestrator
python -m uvicorn app.main:app --host 127.0.0.1 --port 8200
```

```bash
source .venv/bin/activate
cd services/ingest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

```bash
source .venv/bin/activate
cd services/api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd apps/web
corepack pnpm dev --port 3000

Leave `NEXT_PUBLIC_API_BASE_URL` unset or empty so the web app uses the built-in Next.js proxy for `/api/*` requests.
```

## Optional extras

Install richer document parsing and storage adapters when needed:

```bash
source .venv/bin/activate
uv pip install -e services/api[parsers,storage]
```

## Optional infrastructure

```bash
make infra
```

This starts:

- Postgres
- Redis
- Qdrant
- MinIO

## Notes

- The API includes fallback logic, so the product still runs when optional services are unavailable.
- The model gateway defaults to `mock` mode. Switch to `ollama` when the local model stack is installed.
- Best-tested upload path is currently `.txt` and `.md`.
