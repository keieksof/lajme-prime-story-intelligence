from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.models.domain import StoryAnalysis
from app.services.story_graph import StoryGraphService
from app.story_engine.graph import StoryNode, build_edges


def test_previous_development_is_ranked_first() -> None:
    current = StoryNode(
        video_id="current",
        story_id="story-1",
        title="Update",
        published_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        people=frozenset({"person-a"}),
        topics=frozenset({"topic-a"}),
    )
    previous = StoryNode(
        video_id="previous",
        story_id="story-1",
        title="Earlier",
        published_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
        people=frozenset({"person-a"}),
        topics=frozenset({"topic-a"}),
    )

    edges = build_edges(current, [previous])

    assert edges[0].relationship_type == "PREVIOUS_DEVELOPMENT"
    assert edges[0].confidence == 0.95


@dataclass
class FakeCandidate:
    id: object
    canonical_key: str
    analysis: StoryAnalysis


class FakeRepository:
    def __init__(self, candidates: list[FakeCandidate]) -> None:
        self.candidates = candidates
        self.relationships: list[dict] = []

    def find_candidates(self, analysis: StoryAnalysis, limit: int = 50) -> list[FakeCandidate]:
        return self.candidates[:limit]

    def upsert_with_status(self, analysis: StoryAnalysis):
        return SimpleNamespace(id=uuid4()), True

    def upsert_relationship(self, **kwargs):
        self.relationships.append(kwargs)
        return SimpleNamespace(**kwargs)


def make_story(key: str, title: str, people: list[str], topics: list[str]) -> StoryAnalysis:
    return StoryAnalysis(
        canonical_key=key,
        title=title,
        summary=title,
        people=people,
        topics=topics,
    )


def test_graph_links_existing_related_story() -> None:
    previous = make_story("story:old", "Berisha reagon për protestën", ["Sali Berisha"], ["protesta"])
    current = make_story("story:new", "Berisha flet pas protestës", ["Sali Berisha"], ["protesta"])
    repository = FakeRepository([FakeCandidate(uuid4(), previous.canonical_key, previous)])

    result = StoryGraphService(repository).ingest(current)

    assert result.created is True
    assert result.matches[0].relationship_type in {"SAME_STORY", "SAME_PERSON_NEW_DEVELOPMENT"}
    assert repository.relationships


def test_graph_skips_context_only_matches() -> None:
    unrelated = make_story("story:other", "Moti për fundjavën", [], ["moti"])
    current = make_story("story:new", "Berisha flet për protestën", ["Sali Berisha"], ["protesta"])
    repository = FakeRepository([FakeCandidate(uuid4(), unrelated.canonical_key, unrelated)])

    result = StoryGraphService(repository).ingest(current)

    assert result.created is True
    assert result.matches[0].relationship_type == "CONTEXT_ONLY"
    assert repository.relationships == []
