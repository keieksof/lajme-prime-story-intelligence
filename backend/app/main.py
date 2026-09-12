from fastapi import FastAPI

from app.api.routes_embeddings import router as embeddings_router
from app.api.routes_learning import router as learning_router
from app.api.routes_related import router as related_router
from app.api.routes_research import router as research_router
from app.api.routes_story import router as story_router
from app.api.routes_youtube import router as youtube_router

app = FastAPI(
    title="Lajme Prime Story Intelligence",
    version="0.1.0",
)

app.include_router(story_router, prefix="/api")
app.include_router(youtube_router, prefix="/api")
app.include_router(related_router, prefix="/api")
app.include_router(research_router, prefix="/api")
app.include_router(embeddings_router, prefix="/api")
app.include_router(learning_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lajme-prime-story-intelligence"}
