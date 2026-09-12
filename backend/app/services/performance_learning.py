from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import LearningSignalRow, PerformanceMetricRow, PublicationRow, VideoRelationshipRow


@dataclass(frozen=True)
class PerformanceSnapshot:
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    impressions: int | None = None
    ctr: float | None = None
    average_view_duration_seconds: float | None = None
    average_percentage_viewed: float | None = None
    swipe_away_rate: float | None = None
    retention: dict = None
    raw_metrics: dict = None
    captured_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "retention", self.retention or {})
        object.__setattr__(self, "raw_metrics", self.raw_metrics or {})


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _engagement_rate(snapshot: PerformanceSnapshot) -> float | None:
    if snapshot.views is None or snapshot.views <= 0:
        return None
    interactions = sum(
        value or 0
        for value in (snapshot.likes, snapshot.comments, snapshot.shares)
    )
    return _clamp(interactions / snapshot.views)


def performance_outcome(snapshot: PerformanceSnapshot) -> float:
    """Return a bounded -1..1 outcome from a performance snapshot.

    This is intentionally a baseline calibration, not a claim about a platform's
    internal ranking formula. It gives the learning loop a stable signal until
    enough historical Lajme Prime data exists to learn stronger thresholds.
    """
    components: list[tuple[float, float]] = []

    if snapshot.ctr is not None:
        components.append((_clamp(snapshot.ctr / 0.10), 0.25))
    if snapshot.average_percentage_viewed is not None:
        components.append((_clamp(snapshot.average_percentage_viewed / 0.60), 0.30))
    if snapshot.swipe_away_rate is not None:
        components.append((_clamp(1.0 - snapshot.swipe_away_rate), 0.25))

    engagement = _engagement_rate(snapshot)
    if engagement is not None:
        components.append((_clamp(engagement / 0.08), 0.20))

    if not components:
        return 0.0

    weight_total = sum(weight for _, weight in components)
    quality = sum(value * weight for value, weight in components) / weight_total
    return round((quality * 2.0) - 1.0, 5)


def _positive_features(features: dict) -> list[tuple[str, float]]:
    result: list[tuple[str, float]] = []
    for key, value in features.items():
        if key not in {
            "same_story",
            "same_person",
            "same_event",
            "chronological_continuity",
            "reaction_chain",
            "semantic_similarity",
            "same_topic_only",
        }:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric > 0.0:
            result.append((key, max(0.0, min(1.0, numeric))))
    return result


def record_performance_snapshot(
    session: Session,
    *,
    publication_id: UUID,
    snapshot: PerformanceSnapshot,
) -> tuple[PerformanceMetricRow, int]:
    publication = session.get(PublicationRow, publication_id)
    if publication is None:
        raise ValueError("Publication not found")

    metric = PerformanceMetricRow(
        publication_id=publication_id,
        captured_at=snapshot.captured_at or datetime.now().astimezone(),
        views=snapshot.views,
        likes=snapshot.likes,
        comments=snapshot.comments,
        shares=snapshot.shares,
        impressions=snapshot.impressions,
        ctr=snapshot.ctr,
        average_view_duration_seconds=snapshot.average_view_duration_seconds,
        average_percentage_viewed=snapshot.average_percentage_viewed,
        swipe_away_rate=snapshot.swipe_away_rate,
        retention=snapshot.retention,
        raw_metrics=snapshot.raw_metrics,
    )
    session.add(metric)
    session.flush()

    outcome = performance_outcome(snapshot)
    relationships = session.scalars(
        select(VideoRelationshipRow).where(
            VideoRelationshipRow.current_video_id == publication.video_id,
            VideoRelationshipRow.selected.is_(True),
        )
    ).all()

    created_signals = 0
    for relationship in relationships:
        for feature_key, feature_value in _positive_features(relationship.ranking_features):
            session.add(
                LearningSignalRow(
                    publication_id=publication_id,
                    performance_metric_id=metric.id,
                    signal_type="performance_auto",
                    feature_key=feature_key,
                    feature_value={
                        "value": feature_value,
                        "candidate_video_id": str(relationship.candidate_video_id),
                        "relationship_type": relationship.relationship_type,
                        "score": float(relationship.score),
                    },
                    outcome_value=outcome * feature_value,
                    confidence=feature_value,
                )
            )
            created_signals += 1

    return metric, created_signals
