from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class StoryRow(Base):
    __tablename__ = "stories"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    canonical_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    analysis_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    videos: Mapped[list["VideoRow"]] = relationship(back_populates="story")


class VideoRow(Base):
    __tablename__ = "videos"
    __table_args__ = (UniqueConstraint("platform", "external_id"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    transcript: Mapped[str | None] = mapped_column(Text)
    story_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("stories.id", ondelete="SET NULL"))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    story: Mapped[StoryRow | None] = relationship(back_populates="videos")


class StoryRelationshipRow(Base):
    __tablename__ = "story_relationships"
    __table_args__ = (UniqueConstraint("from_story_id", "to_story_id", "relationship_type"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    from_story_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    to_story_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)
    strength: Mapped[float | None] = mapped_column(Numeric(6, 4))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class VideoRelationshipRow(Base):
    __tablename__ = "video_relationships"
    __table_args__ = (UniqueConstraint("current_video_id", "candidate_video_id"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    current_video_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    candidate_video_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    ranking_features: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PublicationRow(Base):
    __tablename__ = "publications"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    video_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    external_url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    related_video_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("videos.id", ondelete="SET NULL"))
    editorial_version: Mapped[str | None] = mapped_column(String(100))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class PerformanceMetricRow(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    publication_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publications.id", ondelete="CASCADE"), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    views: Mapped[int | None] = mapped_column(Integer)
    likes: Mapped[int | None] = mapped_column(Integer)
    comments: Mapped[int | None] = mapped_column(Integer)
    shares: Mapped[int | None] = mapped_column(Integer)
    impressions: Mapped[int | None] = mapped_column(Integer)
    ctr: Mapped[float | None] = mapped_column(Numeric(8, 5))
    average_view_duration_seconds: Mapped[float | None] = mapped_column(Numeric(12, 4))
    average_percentage_viewed: Mapped[float | None] = mapped_column(Numeric(8, 5))
    swipe_away_rate: Mapped[float | None] = mapped_column(Numeric(8, 5))
    retention: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    raw_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class LearningSignalRow(Base):
    __tablename__ = "learning_signals"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    publication_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("publications.id", ondelete="SET NULL"))
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_key: Mapped[str] = mapped_column(String(255), nullable=False)
    feature_value: Mapped[Any | None] = mapped_column(JSON)
    outcome_value: Mapped[float | None] = mapped_column(Numeric(10, 5))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
