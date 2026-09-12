from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import StoryRelationshipRow, StoryRow
from app.models.domain import StoryAnalysis
from app.story_engine.story_matcher import StoryMatch, match_stories


@dataclass(frozen=True)
class StoryResolution:
    story: StoryRow
    match: StoryMatch | None
    created: bool


def choose_best_match(
    analysis: StoryAnalysis,
    candidates: list[StoryAnalysis],
) -> tuple[StoryAnalysis, StoryMatch] | None:
    best: tuple[StoryAnalysis, StoryMatch] | None = None
    for candidate in candidates:
        match = match_stories(analysis, candidate)
        if best is None or match.score > best[1].score:
            best = (candidate, match)
    return best


def resolve_story(session: Session, analysis: StoryAnalysis, candidate_limit: int = 1000) -> StoryResolution:
    exact = session.scalar(
        select(StoryRow).where(StoryRow.canonical_key == analysis.canonical_key)
    )
    if exact is not None:
        return StoryResolution(
            story=_update_story_row(exact, analysis),
            match=StoryMatch("SAME_STORY", 1.0, ["exact canonical story key"]),
            created=False,
        )

    rows = list(
        session.scalars(
            select(StoryRow)
            .where(StoryRow.status == "active")
            .order_by(StoryRow.last_updated_at.desc().nullslast())
            .limit(candidate_limit)
        )
    )
    candidates = [_analysis_from_row(row) for row in rows]
    best = choose_best_match(analysis, candidates)

    if best is not None:
        matched_analysis, match = best
        matched_row = next(row for row in rows if row.id == _story_id_for_analysis(rows, matched_analysis))
        if match.relationship_type == "SAME_STORY" and match.score >= 0.75:
            return StoryResolution(
                story=_update_story_row(matched_row, analysis),
                match=match,
                created=False,
            )

    row = StoryRow(
        canonical_key=analysis.canonical_key,
        title=analysis.title,
        summary=analysis.summary,
        category=analysis.category,
        analysis_json=_analysis_json(analysis),
        first_seen_at=analysis.occurred_at or datetime.now(timezone.utc),
        last_updated_at=analysis.occurred_at or datetime.now(timezone.utc),
    )
    session.add(row)
    session.flush()

    if best is not None:
        matched_analysis, match = best
        matched_row = next(row for row in rows if row.id == _story_id_for_analysis(rows, matched_analysis))
        if match.relationship_type != "CONTEXT_ONLY" and matched_row.id != row.id:
            _save_story_relationship(session, row.id, matched_row.id, match)

    return StoryResolution(story=row, match=best[1] if best else None, created=True)


def _analysis_from_row(row: StoryRow) -> StoryAnalysis:
    payload: dict[str, Any] = row.analysis_json or {}
    return StoryAnalysis(
        canonical_key=row.canonical_key,
        title=row.title,
        summary=row.summary or "",
        category=row.category,
        people=[str(item) for item in payload.get("people", [])],
        organizations=[str(item) for item in payload.get("organizations", [])],
        topics=[str(item) for item in payload.get("topics", [])],
        events=[item for item in payload.get("events", []) if isinstance(item, dict)],
        claims=[item for item in payload.get("claims", []) if isinstance(item, dict)],
        occurred_at=row.last_updated_at,
    )


def _analysis_json(analysis: StoryAnalysis) -> dict[str, Any]:
    return {
        "canonical_key": analysis.canonical_key,
        "title": analysis.title,
        "summary": analysis.summary,
        "category": analysis.category,
        "people": analysis.people,
        "organizations": analysis.organizations,
        "topics": analysis.topics,
        "events": analysis.events,
        "claims": analysis.claims,
        "occurred_at": analysis.occurred_at.isoformat() if analysis.occurred_at else None,
    }


def _update_story_row(row: StoryRow, analysis: StoryAnalysis) -> StoryRow:
    row.title = analysis.title
    row.summary = analysis.summary
    row.category = analysis.category
    row.analysis_json = _analysis_json(analysis)
    row.last_updated_at = analysis.occurred_at or datetime.now(timezone.utc)
    return row


def _story_id_for_analysis(rows: list[StoryRow], analysis: StoryAnalysis) -> UUID:
    for row in rows:
        if row.canonical_key == analysis.canonical_key:
            return row.id
    raise LookupError("candidate story row not found")


def _save_story_relationship(
    session: Session,
    from_story_id: UUID,
    to_story_id: UUID,
    match: StoryMatch,
) -> None:
    existing = session.scalar(
        select(StoryRelationshipRow).where(
            StoryRelationshipRow.from_story_id == from_story_id,
            StoryRelationshipRow.to_story_id == to_story_id,
            StoryRelationshipRow.relationship_type == match.relationship_type,
        )
    )
    if existing is None:
        session.add(
            StoryRelationshipRow(
                from_story_id=from_story_id,
                to_story_id=to_story_id,
                relationship_type=match.relationship_type,
                strength=match.score,
                evidence={"reasons": match.reasons},
            )
        )
    else:
        existing.strength = match.score
        existing.evidence = {"reasons": match.reasons}
