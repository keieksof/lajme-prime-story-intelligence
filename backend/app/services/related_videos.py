from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from app.db_models import VideoRow
from app.story_engine.related_video_ranker import CandidateSignals, classify_relationship, score_candidate


@dataclass(frozen=True)
class RelatedVideoResult:
    video_id: UUID
    title: str
    url: str
    relationship_type: str
    score: float
    features: dict[str, float]


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", value.lower())
        if token not in {"është", "eshte", "dhe", "nga", "për", "per", "këtë", "kete"}
    }


def _overlap(a: str, b: str) -> float:
    left = _tokens(a)
    right = _tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / max(1, len(left | right))


def _graph_signal(relationship_type: str | None) -> CandidateSignals:
    return CandidateSignals(
        same_story=1.0 if relationship_type == "SAME_STORY" else 0.0,
        same_event=1.0
        if relationship_type in {"SAME_STORY", "FOLLOW_UP", "PREVIOUS_DEVELOPMENT"}
        else 0.0,
        reaction_chain=1.0 if relationship_type == "REACTION_CHAIN" else 0.0,
        same_person=1.0 if relationship_type == "SAME_PERSON_NEW_DEVELOPMENT" else 0.0,
        same_topic_only=1.0 if relationship_type == "SAME_TOPIC_NOT_SAME_STORY" else 0.0,
    )


def rank_related_videos(
    current: VideoRow,
    candidates: list[VideoRow],
    limit: int = 5,
    graph_relationships: dict[UUID, str] | None = None,
    semantic_similarities: dict[UUID, float] | None = None,
) -> list[RelatedVideoResult]:
    results: list[RelatedVideoResult] = []
    graph_relationships = graph_relationships or {}
    semantic_similarities = semantic_similarities or {}

    for candidate in candidates:
        if (
            candidate.id == current.id
            or candidate.published_at is None
            or current.published_at is None
        ):
            continue
        if candidate.published_at > current.published_at:
            continue

        lexical = _overlap(current.title, candidate.title)
        same_story = 1.0 if current.story_id and current.story_id == candidate.story_id else 0.0
        chronology = 1.0 if candidate.published_at <= current.published_at else 0.0
        semantic_similarity = semantic_similarities.get(
            candidate.id,
            _overlap(
                f"{current.title} {current.description or ''}",
                f"{candidate.title} {candidate.description or ''}",
            ),
        )
        graph_type = graph_relationships.get(candidate.story_id) if candidate.story_id else None
        graph_signals = _graph_signal(graph_type)

        signals = CandidateSignals(
            same_story=max(same_story, graph_signals.same_story),
            same_person=max(min(1.0, lexical * 1.2), graph_signals.same_person),
            same_event=max(same_story, graph_signals.same_event),
            chronological_continuity=chronology,
            reaction_chain=graph_signals.reaction_chain,
            semantic_similarity=semantic_similarity,
            same_topic_only=max(min(1.0, lexical), graph_signals.same_topic_only),
        )
        score = score_candidate(signals)
        relationship = graph_type or classify_relationship(signals)

        if signals.same_story == 0.0 and score < 25:
            continue

        results.append(
            RelatedVideoResult(
                video_id=candidate.id,
                title=candidate.title,
                url=candidate.url,
                relationship_type=relationship,
                score=round(score, 4),
                features={
                    "same_story": signals.same_story,
                    "title_overlap": lexical,
                    "semantic_similarity": semantic_similarity,
                    "chronological_continuity": chronology,
                    "graph_relationship": 1.0 if graph_type else 0.0,
                },
            )
        )

    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]
