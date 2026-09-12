from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import StoryRow, VideoRow
from app.ingestion.youtube import YouTubeVideo


class YouTubeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_video(self, video: YouTubeVideo, story_id: str | None = None) -> VideoRow:
        row = self.session.scalar(
            select(VideoRow).where(
                VideoRow.platform == "youtube",
                VideoRow.external_id == video.external_id,
            )
        )
        if row is None:
            row = VideoRow(
                platform="youtube",
                external_id=video.external_id,
                url=video.url,
                title=video.title,
                description=video.description,
                published_at=video.published_at,
                duration_seconds=video.duration_seconds,
                story_id=story_id,
                metadata_json=video.raw,
            )
            self.session.add(row)
        else:
            row.url = video.url
            row.title = video.title
            row.description = video.description
            row.published_at = video.published_at
            row.duration_seconds = video.duration_seconds
            row.metadata_json = video.raw
            if story_id:
                row.story_id = story_id
        self.session.flush()
        return row

    def list_recent(self, limit: int = 50) -> list[VideoRow]:
        return list(
            self.session.scalars(
                select(VideoRow)
                .where(VideoRow.platform == "youtube")
                .order_by(VideoRow.published_at.desc().nullslast())
                .limit(limit)
            )
        )
