# Local Development

## Services

- Web: `apps/web`
- API: `services/api`
- Ingest: `services/ingest`
- Orchestrator: `services/orchestrator`
- Model gateway: `services/model-gateway`
- Infra: `infra/compose/local.yml`

## Commands

```bash
make infra
make api
make web
make ingest
make orchestrator
make model-gateway
```

## Environment

Copy `.env.example` to `.env` and update values as needed.

## Notes

- The API currently includes a heuristic in-process research pipeline so the prototype can run before local model dependencies are installed.
- The model gateway defaults to `mock` mode. Switch it to `ollama` once the local model stack is available.
- Richer PDF/DOCX/PPTX parsing via `docling` is optional. Install the API `parsers` extra when you need that capability.
