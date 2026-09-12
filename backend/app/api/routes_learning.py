from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.db import SessionLocal
from app.db_models import LearningSignalRow
from app.learning.adaptive_ranker import BASE_WEIGHTS, derive_adaptive_weights

router = APIRouter(prefix="/learning", tags=["learning"])


class LearningFeedback(BaseModel):
    feature_key: str = Field(min_length=1, max_length=255)
    outcome: float = Field(ge=-1.0, le=1.0)
    signal_type: str = Field(default="related_video_outcome", min_length=1, max_length=100)
    publication_id: UUID | None = None
    feature_value: dict[str, Any] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


@router.post("/feedback")
def record_feedback(payload: LearningFeedback) -> dict[str, Any]:
    with SessionLocal() as session:
        row = LearningSignalRow(
            publication_id=payload.publication_id,
            signal_type=payload.signal_type,
            feature_key=payload.feature_key,
            feature_value=payload.feature_value,
            outcome_value=payload.outcome,
            confidence=payload.confidence,
        )
        session.add(row)
        session.commit()
        weights = derive_adaptive_weights(session)
    return {"feature_key": payload.feature_key, "outcome": payload.outcome, "weights": weights.values}


@router.get("/weights")
def get_weights(
    minimum_samples: int = Query(5, ge=1, le=1000),
) -> dict[str, Any]:
    with SessionLocal() as session:
        adaptive = derive_adaptive_weights(session, minimum_samples=minimum_samples)
    return {"base": BASE_WEIGHTS, "adaptive": adaptive.values, "samples": adaptive.samples}
