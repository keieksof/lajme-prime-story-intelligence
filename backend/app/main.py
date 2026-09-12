from fastapi import FastAPI

from app.api.routes_story import router as story_router

app = FastAPI(
    title="Lajme Prime Story Intelligence",
    version="0.1.0",
)

app.include_router(story_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lajme-prime-story-intelligence"}
