from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.db_models import VideoRow


def find_semantic_candidates(
    session: Session,
    current: VideoRow,
    *,
    limit: int = 100,
) -> dict[UUID, float]:
    """Return historical candidates keyed by video id with cosine similarity."""
    if not current.embedding or current.published_at is None:
        return {}

    distance = VideoRow.embedding.cosine_distance(current.embedding).label("distance")
    rows = session.execute(
        select(VideoRow, distance)
        .where(
            VideoRow.platform == current.platform,
            VideoRow.id != current.id,
            VideoRow.published_at.is_not(None),
            VideoRow.published_at <= current.published_at,
            VideoRow.embedding.is_not(None),
        )
        .order_by(distance.asc())
        .limit(limit)
    ).all()

    return {
        row.id: max(0.0, min(1.0, 1.0 - float(distance_value)))
        for row, distance_value in rows
    }
