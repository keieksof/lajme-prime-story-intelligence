from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import StoryRelationshipRow, StoryRow
from app.models.domain import StoryAnalysis
from app.story_engine.story_matcher import StoryMatch, match_stories


class StoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_with_status(self, analysis: StoryAnalysis) -> tuple[StoryRow, bool]:
        row = self.session.scalar(
            select(StoryRow).where(StoryRow.canonical_key == analysis.canonical_key)
        )
        now = datetime.now(timezone.utc)
        payload = _analysis_metadata(analysis)
        created = row is None

        if row is None:
            row = StoryRow(
                canonical_key=analysis.canonical_key,
                title=analysis.title,
                summary=analysis.summary,
                category=analysis.category,
                analysis_json=payload,
                first_seen_at=analysis.occurred_at or now,
                last_updated_at=analysis.occurred_at or now,
            )
            self.session.add(row)
        else:
            row.title = analysis.title
            row.summary = analysis.summary
            row.category = analysis.category
            row.analysis_json = payload
            row.last_updated_at = analysis.occurred_at or now
        self.session.flush()
        return row, created

    def upsert(self, analysis: StoryAnalysis) -> StoryRow:
        row, _ = self.upsert_with_status(analysis)
        return row

    def find_candidates(self, analysis: StoryAnalysis, limit: int = 50) -> list[StoryGraphCandidate]:
        rows = self.session.scalars(
            select(StoryRow)
            .where(StoryRow.status == "active")
            .order_by(StoryRow.last_updated_at.desc().nullslast())
            .limit(limit)
        ).all()
        candidates: list[StoryGraphCandidate] = []
        for row in rows:
            candidate_analysis = _analysis_from_row(row)
            if candidate_analysis is None:
                continue
            candidates.append(
                StoryGraphCandidate(
                    id=row.id,
                    canonical_key=row.canonical_key,
                    analysis=candidate_analysis,
                )
            )
        candidates.sort(
            key=lambda item: match_stories(analysis, item.analysis).score,
            reverse=True,
        )
        return candidates

    def find_matches(self, analysis: StoryAnalysis, limit: int = 50) -> list[StoryMatch]:
        matches = [
            match_stories(analysis, candidate.analysis)
            for candidate in self.find_candidates(analysis, limit=limit)
            if candidate.canonical_key != analysis.canonical_key
        ]
        return sorted(matches, key=lambda item: item.score, reverse=True)

    def upsert_relationship(
        self,
        from_story_id: UUID,
        to_story_id: UUID,
        relationship_type: str,
        strength: float,
        evidence: dict,
    ) -> StoryRelationshipRow:
        row = self.session.scalar(
            select(StoryRelationshipRow).where(
                StoryRelationshipRow.from_story_id == from_story_id,
                StoryRelationshipRow.to_story_id == to_story_id,
                StoryRelationshipRow.relationship_type == relationship_type,
            )
        )
        if row is None:
            row = StoryRelationshipRow(
                from_story_id=from_story_id,
                to_story_id=to_story_id,
                relationship_type=relationship_type,
                strength=strength,
                evidence=evidence,
            )
            self.session.add(row)
        else:
            row.strength = strength
            row.evidence = evidence
        self.session.flush()
        return row

    def get(self, story_id: UUID) -> StoryRow | None:
        return self.session.get(StoryRow, story_id)


class StoryGraphCandidate:
    def __init__(self, id: UUID, canonical_key: str, analysis: StoryAnalysis) -> None:
        self.id = id
        self.canonical_key = canonical_key
        self.analysis = analysis


def _analysis_metadata(analysis: StoryAnalysis) -> dict:
    return {
        "people": analysis.people,
        "organizations": analysis.organizations,
        "topics": analysis.topics,
        "events": analysis.events,
        "claims": analysis.claims,
        "occurred_at": analysis.occurred_at.isoformat() if analysis.occurred_at else None,
    }


def _analysis_from_row(row: StoryRow) -> StoryAnalysis | None:
    metadata = row.analysis_json or {}
    if not isinstance(metadata, dict):
        return None
    occurred_at = metadata.get("occurred_at")
    parsed_occurred_at = None
    if isinstance(occurred_at, str) and occurred_at:
        try:
            parsed_occurred_at = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        except ValueError:
            parsed_occurred_at = None
    return StoryAnalysis(
        canonical_key=row.canonical_key,
        title=row.title,
        summary=row.summary or "",
        category=row.category,
        people=_string_list(metadata.get("people")),
        organizations=_string_list(metadata.get("organizations")),
        topics=_string_list(metadata.get("topics")),
        events=_dict_list(metadata.get("events")),
        claims=_dict_list(metadata.get("claims")),
        occurred_at=parsed_occurred_at,
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dict_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
