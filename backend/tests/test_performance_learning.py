from __future__ import annotations

from app.services.performance_learning import PerformanceSnapshot, performance_outcome


def test_performance_outcome_is_bounded() -> None:
    weak = performance_outcome(
        PerformanceSnapshot(
            ctr=0.0,
            average_percentage_viewed=0.0,
            swipe_away_rate=1.0,
            views=1000,
            likes=0,
            comments=0,
            shares=0,
        )
    )
    strong = performance_outcome(
        PerformanceSnapshot(
            ctr=0.10,
            average_percentage_viewed=0.60,
            swipe_away_rate=0.0,
            views=1000,
            likes=80,
            comments=0,
            shares=0,
        )
    )

    assert weak == -1.0
    assert strong == 1.0


def test_performance_outcome_is_neutral_without_metrics() -> None:
    assert performance_outcome(PerformanceSnapshot()) == 0.0


def test_snapshot_keeps_optional_json_payloads_initialized() -> None:
    snapshot = PerformanceSnapshot()
    assert snapshot.retention == {}
    assert snapshot.raw_metrics == {}
