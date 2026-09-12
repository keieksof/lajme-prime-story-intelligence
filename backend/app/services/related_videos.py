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


def rank_related_videos(current: VideoRow, candidates: list[VideoRow], limit: int = 5) -> list[RelatedVideoResult]:
    results: list[RelatedVideoResult] = []
    for candidate in candidates:
        if candidate.id == current.id or candidate.published_at is None or current.published_at is None:
            continue
        if candidate.published_at > current.published_at:
            continue

        lexical = _overlap(current.title, candidate.title)
        same_story = 1.0 if current.story_id and current.story_id == candidate.story_id else 0.0
        chronology = 1.0 if candidate.published_at <= current.published_at else 0.0
        semantic_proxy = _overlap(
            f"{current.title} {current.description or ''}",
            f"{candidate.title} {candidate.description or ''}",
        )

        signals = CandidateSignals(
            same_story=same_story,
            same_person=min(1.0, lexical * 1.2),
            same_event=same_story,
            chronological_continuity=chronology,
            reaction_chain=0.0,
            semantic_similarity=semantic_proxy,
            same_topic_only=min(1.0, lexical),
        )
        score = score_candidate(signals)
        relationship = classify_relationship(signals)

        # Do not surface weak generic matches as editorially related.
        if same_story == 0.0 and score < 25:
            continue

        results.append(
            RelatedVideoResult(
                video_id=candidate.id,
                title=candidate.title,
                url=candidate.url,
                relationship_type=relationship,
                score=round(score, 4),
                features={
                    "same_story": same_story,
                    "title_overlap": lexical,
                    "semantic_proxy": semantic_proxy,
                    "chronological_continuity": chronology,
                },
            )
        )

    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]
