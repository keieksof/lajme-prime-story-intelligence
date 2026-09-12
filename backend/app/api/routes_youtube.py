import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.db import SessionLocal
from app.db_models import VideoRow
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
        "embeddings_created": result.embeddings_created,
        "stories_created": result.stories_created,
        "stories_reused": result.stories_reused,
    }


@router.get("/recent")
def recent_videos(limit: int = Query(25, ge=1, le=100)) -> dict[str, list[dict[str, Any]]]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(VideoRow)
            .where(VideoRow.platform == "youtube")
            .order_by(VideoRow.published_at.desc().nullslast())
            .limit(limit)
        ).all()
    return {
        "videos": [
            {
                "id": str(row.id),
                "external_id": row.external_id,
                "title": row.title,
                "url": row.url,
                "thumbnail_url": f"https://i.ytimg.com/vi/{row.external_id}/hqdefault.jpg" if row.external_id else None,
                "description": row.description,
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "story_id": str(row.story_id) if row.story_id else None,
            }
            for row in rows
        ]
    }
