from fastapi import FastAPI

from app.config import get_settings
from app.providers import catalog, embed, generate
from app.schemas import EmbedRequest, EmbedResponse, GenerateRequest, GenerateResponse, ModelCatalogResponse

settings = get_settings()
app = FastAPI(title="Learnable Model Gateway", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "learnable-model-gateway",
        "mode": settings.learnable_model_gateway_mode,
    }


@app.get("/models", response_model=ModelCatalogResponse)
def models() -> ModelCatalogResponse:
    return catalog(settings)


@app.post("/v1/generate", response_model=GenerateResponse)
def generate_text(body: GenerateRequest) -> GenerateResponse:
    return generate(body, settings)


@app.post("/v1/embed", response_model=EmbedResponse)
def embed_text(body: EmbedRequest) -> EmbedResponse:
    payload = embed(body.inputs, body.normalize, settings)
    return EmbedResponse(**payload)
