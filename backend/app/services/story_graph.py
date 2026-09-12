from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.domain import StoryAnalysis
from app.repositories.story_repository import StoryRepository
from app.story_engine.story_matcher import StoryMatch, match_stories


@dataclass(frozen=True)
class StoryGraphResult:
    story_id: str
    created: bool
    matches: list[StoryMatch]


class StoryGraphService:
    """Persist a story and connect it to the existing story graph."""

    def __init__(self, repository: StoryRepository) -> None:
        self.repository = repository

    def ingest(self, analysis: StoryAnalysis, max_candidates: int = 50) -> StoryGraphResult:
        candidates = self.repository.find_candidates(analysis, limit=max_candidates)
        matches: list[StoryMatch] = []

        for candidate in candidates:
            if candidate.canonical_key == analysis.canonical_key:
                continue
            matches.append(match_stories(analysis, candidate.analysis))

        matches.sort(key=lambda item: item.score, reverse=True)
        row, created = self.repository.upsert_with_status(analysis)

        for candidate in candidates:
            if candidate.canonical_key == analysis.canonical_key:
                continue
            match = match_stories(analysis, candidate.analysis)
            if match.relationship_type == "CONTEXT_ONLY":
                continue
            self.repository.upsert_relationship(
                from_story_id=row.id,
                to_story_id=candidate.id,
                relationship_type=match.relationship_type,
                strength=match.score,
                evidence={"reasons": match.reasons},
            )

        return StoryGraphResult(
            story_id=str(row.id),
            created=created,
            matches=matches,
        )


def serialize_graph_result(result: StoryGraphResult) -> dict[str, Any]:
    return {
        "story_id": result.story_id,
        "created": result.created,
        "matches": [
            {
                "relationship_type": match.relationship_type,
                "score": match.score,
                "reasons": match.reasons,
            }
            for match in result.matches
        ],
    }
