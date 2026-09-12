from fastapi import APIRouter, HTTPException, Query

from app.ingestion.service import ingest_youtube_channel

router = APIRouter(prefix="/youtube", tags=["youtube"])


@router.post("/ingest")
async def ingest(channel: str = Query(..., description="YouTube channel ID or handle"), limit: int = Query(25, ge=1, le=200)) -> dict:
    try:
        videos = await ingest_youtube_channel(channel, limit=limit)
    except (RuntimeError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"channel": channel, "count": len(videos), "videos": videos}
