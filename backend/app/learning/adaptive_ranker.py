from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db_models import LearningSignalRow


BASE_WEIGHTS = {
    "same_story": 40.0,
    "same_person": 20.0,
    "same_event": 20.0,
    "chronological_continuity": 20.0,
    "reaction_chain": 15.0,
    "semantic_similarity": 10.0,
    "same_topic_only": 5.0,
}


@dataclass(frozen=True)
class AdaptiveWeights:
    values: dict[str, float]
    samples: dict[str, int]


def derive_adaptive_weights(
    session: Session,
    *,
    minimum_samples: int = 5,
    max_adjustment: float = 0.35,
) -> AdaptiveWeights:
    values = dict(BASE_WEIGHTS)
    samples = {key: 0 for key in BASE_WEIGHTS}

    rows = session.execute(
        select(
            LearningSignalRow.feature_key,
            func.avg(LearningSignalRow.outcome_value),
            func.count(LearningSignalRow.id),
        )
        .where(LearningSignalRow.feature_key.in_(list(BASE_WEIGHTS)))
        .group_by(LearningSignalRow.feature_key)
    ).all()

    for feature_key, mean_outcome, sample_count in rows:
        samples[feature_key] = int(sample_count)
        if sample_count < minimum_samples or mean_outcome is None:
            continue
        centered = max(-1.0, min(1.0, float(mean_outcome)))
        adjustment = max(-max_adjustment, min(max_adjustment, centered * max_adjustment))
        values[feature_key] = round(BASE_WEIGHTS[feature_key] * (1.0 + adjustment), 4)

    return AdaptiveWeights(values=values, samples=samples)
