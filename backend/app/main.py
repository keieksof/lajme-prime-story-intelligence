from fastapi import FastAPI

app = FastAPI(
    title="Lajme Prime Story Intelligence",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lajme-prime-story-intelligence"}
