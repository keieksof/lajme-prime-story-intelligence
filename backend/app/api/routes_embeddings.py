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
    batch_size: int = Query(50, ge=1, le=200),
) -> dict[str, int]:
    processed = 0
    created = 0
    service = OpenAIEmbeddingService()

    with SessionLocal() as session:
        while processed < limit:
            remaining = min(batch_size, limit - processed)
            videos = list(
                session.scalars(
                    select(VideoRow)
                    .where(VideoRow.embedding.is_(None))
                    .order_by(VideoRow.published_at.desc().nullslast())
                    .limit(remaining)
                )
            )
            if not videos:
                break

            try:
                created_now = embed_missing_videos(
                    session,
                    videos,
                    service=service,
                    batch_size=batch_size,
                )
                session.commit()
            except Exception as exc:
                session.rollback()
                raise HTTPException(status_code=502, detail=f"Embedding provider error: {exc}") from exc

            processed += len(videos)
            created += created_now

    return {"processed": processed, "embeddings_created": created}
