from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class StoryCandidate:
    video_id: str
    relationship_type: str
    score: float
    features: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryAnalysis:
    canonical_key: str
    title: str
    summary: str
    category: str | None = None
    people: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    claims: list[dict[str, Any]] = field(default_factory=list)
    occurred_at: datetime | None = None


@dataclass
class LearningSignal:
    feature_key: str
    outcome: float
    signal_type: str
    publication_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
