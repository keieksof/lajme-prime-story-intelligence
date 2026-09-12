from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.db import SessionLocal
from app.ingestion.transcript import TranscriptFetcher
from app.ingestion.youtube import YouTubeClient
from app.models.domain import StoryAnalysis
from app.repositories.story_repository import StoryRepository
from app.repositories.youtube_repository import YouTubeRepository
from app.story_engine.analyzer import HeuristicStoryAnalyzer
from app.story_engine.llm_analyzer import LLMStoryAnalyzer
from app.story_engine.pipeline import StoryIntelligencePipeline


@dataclass(frozen=True)
class IngestionResult:
    imported: int
    updated: int
    transcripts_fetched: int
    stories_created: int
    stories_reused: int


def _build_analyzer() -> HeuristicStoryAnalyzer | LLMStoryAnalyzer:
    mode = os.getenv("STORY_ANALYZER", "heuristic").strip().lower()
    if mode == "llm":
        return LLMStoryAnalyzer()
    return HeuristicStoryAnalyzer()


async def ingest_channel(api_key: str, channel: str, limit: int = 50) -> IngestionResult:
    client = YouTubeClient(api_key=api_key)
    videos = await client.list_uploads(channel, limit=limit)
    pipeline = StoryIntelligencePipeline(_build_analyzer())
    transcript_fetcher = TranscriptFetcher()

    imported = 0
    updated = 0
    transcripts_fetched = 0
    stories_created = 0
    stories_reused = 0

    with SessionLocal() as session:
        video_repo = YouTubeRepository(session)
        story_repo = StoryRepository(session)
        existing_rows = {
            row.external_id: row
            for row in video_repo.list_recent(limit=max(limit, 200))
        }

        for video in videos:
            existing = existing_rows.get(video.external_id)
            transcript = existing.transcript if existing and existing.transcript else None
            if not transcript:
                transcript = transcript_fetcher.fetch(video.external_id)
                if transcript:
                    transcripts_fetched += 1

            analysis_text = "\n".join(
                value for value in (video.title, video.description, transcript) if value
            )
            analysis = pipeline.process(
                title=video.title,
                text=analysis_text,
                source_url=video.url,
            ).analysis
            story, story_created = story_repo.upsert_with_status(
                _analysis_from_dict(analysis)
            )
            if story_created:
                stories_created += 1
            else:
                stories_reused += 1

            row = video_repo.upsert_video(video, story_id=story.id)
            if transcript:
                row.transcript = transcript

            if existing is None:
                imported += 1
            else:
                updated += 1

        session.commit()

    return IngestionResult(
        imported=imported,
        updated=updated,
        transcripts_fetched=transcripts_fetched,
        stories_created=stories_created,
        stories_reused=stories_reused,
    )


def _analysis_from_dict(value: dict[str, Any]) -> StoryAnalysis:
    occurred_at = value.get("occurred_at")
    parsed_occurred_at = None
    if isinstance(occurred_at, str) and occurred_at.strip():
        try:
            parsed_occurred_at = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        except ValueError:
            parsed_occurred_at = None

    return StoryAnalysis(
        canonical_key=str(value["canonical_key"]),
        title=str(value["title"]),
        summary=str(value["summary"]),
        category=value.get("category"),
        people=[str(item) for item in value.get("people", [])],
        organizations=[str(item) for item in value.get("organizations", [])],
        topics=[str(item) for item in value.get("topics", [])],
        events=[item for item in value.get("events", []) if isinstance(item, dict)],
        claims=[item for item in value.get("claims", []) if isinstance(item, dict)],
        occurred_at=parsed_occurred_at,
    )
