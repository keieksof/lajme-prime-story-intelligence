from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import StoryRow
from app.models.domain import StoryAnalysis


class StoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, analysis: StoryAnalysis) -> StoryRow:
        row = self.session.scalar(
            select(StoryRow).where(StoryRow.canonical_key == analysis.canonical_key)
        )
        now = datetime.now(timezone.utc)
        if row is None:
            row = StoryRow(
                canonical_key=analysis.canonical_key,
                title=analysis.title,
                summary=analysis.summary,
                category=analysis.category,
                first_seen_at=analysis.occurred_at or now,
                last_updated_at=analysis.occurred_at or now,
            )
            self.session.add(row)
        else:
            row.title = analysis.title
            row.summary = analysis.summary
            row.category = analysis.category
            row.last_updated_at = analysis.occurred_at or now
        self.session.flush()
        return row

    def get(self, story_id: UUID) -> StoryRow | None:
        return self.session.get(StoryRow, story_id)
