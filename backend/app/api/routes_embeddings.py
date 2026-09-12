from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.db import SessionLocal
from app.db_models import VideoRow
from app.services.embeddings import OpenAIEmbeddingService, embed_missing_videos

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post("/backfill")
def backfill_embeddings(
    limit: int = Query(250, ge=1, le=2000),
) -> dict[str, int]:
    with SessionLocal() as session:
        videos = list(
            session.scalars(
                select(VideoRow)
                .where(VideoRow.embedding.is_(None))
                .order_by(VideoRow.published_at.desc().nullslast())
                .limit(limit)
            )
        )
        if not videos:
            return {"processed": 0, "embeddings_created": 0}
        try:
            created = embed_missing_videos(session, videos, service=OpenAIEmbeddingService())
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Embedding provider error: {exc}") from exc
        session.commit()
    return {"processed": len(videos), "embeddings_created": created}
