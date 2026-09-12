from __future__ import annotations

from collections import defaultdict


class FeedbackLearner:
    """Small, persistent-learning-ready baseline.

    This does not retrain the base LLM. It aggregates observed outcomes by
    feature so later ranking decisions can use evidence from Lajme Prime's
    own publication history.
    """

    def __init__(self) -> None:
        self._totals: dict[str, float] = defaultdict(float)
        self._counts: dict[str, int] = defaultdict(int)

    def record(self, feature_key: str, outcome: float) -> None:
        self._totals[feature_key] += outcome
        self._counts[feature_key] += 1

    def mean_outcome(self, feature_key: str) -> float | None:
        count = self._counts.get(feature_key, 0)
        if not count:
            return None
        return self._totals[feature_key] / count

    def evidence(self, feature_key: str) -> dict[str, float | int | None]:
        count = self._counts.get(feature_key, 0)
        return {
            "sample_size": count,
            "mean_outcome": self.mean_outcome(feature_key),
        }
