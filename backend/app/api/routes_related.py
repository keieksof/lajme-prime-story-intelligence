from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.db import SessionLocal
from app.db_models import StoryRelationshipRow, VideoRow, VideoRelationshipRow
from app.services.related_videos import rank_related_videos
from app.services.semantic_retrieval import find_semantic_candidates

router = APIRouter(prefix="/related", tags=["related"])


@router.get("/videos/{video_id}")
def related_videos(
    video_id: UUID,
    limit: int = Query(5, ge=1, le=20),
) -> dict:
    with SessionLocal() as session:
        current = session.get(VideoRow, video_id)
        if current is None:
            raise HTTPException(status_code=404, detail="Video not found")

        semantic_similarities = find_semantic_candidates(
            session,
            current,
            limit=max(50, limit * 10),
        )
        semantic_ids = set(semantic_similarities)

        fallback_candidates = list(
            session.scalars(
                select(VideoRow)
                .where(VideoRow.platform == current.platform, VideoRow.id != video_id)
                .order_by(VideoRow.published_at.desc().nullslast())
                .limit(500)
            )
        )
        candidate_map = {candidate.id: candidate for candidate in fallback_candidates}
        if semantic_ids:
            semantic_rows = list(
                session.scalars(select(VideoRow).where(VideoRow.id.in_(semantic_ids)))
            )
            candidate_map.update({candidate.id: candidate for candidate in semantic_rows})
        candidates = list(candidate_map.values())

        graph_relationships: dict[UUID, str] = {}
        if current.story_id:
            relationships = session.scalars(
                select(StoryRelationshipRow).where(
                    StoryRelationshipRow.from_story_id == current.story_id,
                )
            ).all()
            for relationship in relationships:
                graph_relationships[relationship.to_story_id] = relationship.relationship_type

        ranked = rank_related_videos(
            current,
            candidates,
            limit=limit,
            graph_relationships=graph_relationships,
            semantic_similarities=semantic_similarities,
        )

        session.query(VideoRelationshipRow).filter(
            VideoRelationshipRow.current_video_id == video_id
        ).update({"selected": False})

        for index, item in enumerate(ranked):
            relation = session.scalar(
                select(VideoRelationshipRow).where(
                    VideoRelationshipRow.current_video_id == video_id,
                    VideoRelationshipRow.candidate_video_id == item.video_id,
                )
            )
            if relation is None:
                relation = VideoRelationshipRow(
                    current_video_id=video_id,
                    candidate_video_id=item.video_id,
                    relationship_type=item.relationship_type,
                    score=item.score,
                    ranking_features=item.features,
                    selected=index == 0,
                )
                session.add(relation)
            else:
                relation.relationship_type = item.relationship_type
                relation.score = item.score
                relation.ranking_features = item.features
                relation.selected = index == 0

        session.commit()

    return {
        "video_id": str(video_id),
        "count": len(ranked),
        "candidates": [
            {
                "video_id": str(item.video_id),
                "title": item.title,
                "url": item.url,
                "relationship_type": item.relationship_type,
                "score": item.score,
                "features": item.features,
            }
            for item in ranked
        ],
    }
