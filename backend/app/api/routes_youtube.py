from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query

from app.services.youtube_ingestion import ingest_channel

router = APIRouter(prefix="/youtube", tags=["youtube"])


@router.post("/ingest")
async def ingest(
    channel: str = Query("@LajmePrime", min_length=1, description="YouTube channel ID or handle"),
    limit: int = Query(200, ge=1, le=1000),
) -> dict[str, int | str]:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="YOUTUBE_API_KEY is not configured")
    try:
        result = await ingest_channel(api_key=api_key, channel=channel, limit=limit)
    except (RuntimeError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "channel": channel,
        "imported": result.imported,
        "updated": result.updated,
        "transcripts_fetched": result.transcripts_fetched,
    }
