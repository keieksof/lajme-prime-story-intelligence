from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import SessionLocal
from app.services.performance_learning import PerformanceSnapshot, record_performance_snapshot

router = APIRouter(prefix="/performance", tags=["performance"])


class PerformanceMetricsPayload(BaseModel):
    publication_id: UUID
    captured_at: datetime | None = None
    views: int | None = Field(default=None, ge=0)
    likes: int | None = Field(default=None, ge=0)
    comments: int | None = Field(default=None, ge=0)
    shares: int | None = Field(default=None, ge=0)
    impressions: int | None = Field(default=None, ge=0)
    ctr: float | None = Field(default=None, ge=0.0, le=1.0)
    average_view_duration_seconds: float | None = Field(default=None, ge=0.0)
    average_percentage_viewed: float | None = Field(default=None, ge=0.0, le=1.0)
    swipe_away_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    retention: dict[str, Any] = Field(default_factory=dict)
    raw_metrics: dict[str, Any] = Field(default_factory=dict)


@router.post("/snapshot")
def ingest_performance_snapshot(payload: PerformanceMetricsPayload) -> dict[str, Any]:
    with SessionLocal() as session:
        try:
            metric, signals_created = record_performance_snapshot(
                session,
                publication_id=payload.publication_id,
                snapshot=PerformanceSnapshot(
                    captured_at=payload.captured_at,
                    views=payload.views,
                    likes=payload.likes,
                    comments=payload.comments,
                    shares=payload.shares,
                    impressions=payload.impressions,
                    ctr=payload.ctr,
                    average_view_duration_seconds=payload.average_view_duration_seconds,
                    average_percentage_viewed=payload.average_percentage_viewed,
                    swipe_away_rate=payload.swipe_away_rate,
                    retention=payload.retention,
                    raw_metrics=payload.raw_metrics,
                ),
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        session.commit()

    return {
        "metric_id": str(metric.id),
        "publication_id": str(payload.publication_id),
        "captured_at": metric.captured_at.isoformat(),
        "learning_signals_created": signals_created,
    }
