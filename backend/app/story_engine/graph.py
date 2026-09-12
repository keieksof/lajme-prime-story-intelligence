from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StoryNode:
    video_id: str
    story_id: str | None
    title: str
    published_at: datetime | None
    people: frozenset[str]
    topics: frozenset[str]


@dataclass(frozen=True)
class StoryEdge:
    source_video_id: str
    target_video_id: str
    relationship_type: str
    confidence: float


def build_edges(current: StoryNode, candidates: list[StoryNode]) -> list[StoryEdge]:
    edges: list[StoryEdge] = []
    for candidate in candidates:
        if candidate.video_id == current.video_id:
            continue

        same_story = bool(current.story_id and candidate.story_id and current.story_id == candidate.story_id)
        same_person = bool(current.people & candidate.people)
        same_topic = bool(current.topics & candidate.topics)
        chronological = bool(
            current.published_at and candidate.published_at and candidate.published_at < current.published_at
        )

        if same_story and chronological:
            edges.append(StoryEdge(current.video_id, candidate.video_id, "PREVIOUS_DEVELOPMENT", 0.95))
        elif same_story:
            edges.append(StoryEdge(current.video_id, candidate.video_id, "SAME_STORY", 0.90))
        elif same_person and chronological:
            edges.append(StoryEdge(current.video_id, candidate.video_id, "SAME_PERSON_NEW_DEVELOPMENT", 0.70))
        elif same_person and same_topic:
            edges.append(StoryEdge(current.video_id, candidate.video_id, "REACTION_CHAIN", 0.65))
        elif same_topic:
            edges.append(StoryEdge(current.video_id, candidate.video_id, "SAME_TOPIC_NOT_SAME_STORY", 0.35))

    return sorted(edges, key=lambda edge: edge.confidence, reverse=True)
