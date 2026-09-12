from __future__ import annotations

from dataclasses import dataclass

from app.db import SessionLocal
from app.ingestion.transcript import TranscriptFetcher
from app.ingestion.youtube import YouTubeClient
from app.repositories.story_repository import StoryRepository
from app.repositories.youtube_repository import YouTubeRepository
from app.story_engine.analyzer import HeuristicStoryAnalyzer
from app.story_engine.pipeline import StoryIntelligencePipeline


@dataclass(frozen=True)
class IngestionResult:
    imported: int
    updated: int
    transcripts_fetched: int


async def ingest_channel(api_key: str, channel: str, limit: int = 50) -> IngestionResult:
    client = YouTubeClient(api_key=api_key)
    videos = await client.list_uploads(channel, limit=limit)
    pipeline = StoryIntelligencePipeline(HeuristicStoryAnalyzer())
    transcript_fetcher = TranscriptFetcher()

    imported = 0
    updated = 0
    transcripts_fetched = 0

    with SessionLocal() as session:
        video_repo = YouTubeRepository(session)
        story_repo = StoryRepository(session)
        existing_rows = {row.external_id: row for row in video_repo.list_recent(limit=max(limit, 200))}

        for video in videos:
            existing = existing_rows.get(video.external_id)
            transcript = existing.transcript if existing and existing.transcript else None
            if not transcript:
                transcript = transcript_fetcher.fetch(video.external_id)
                if transcript:
                    transcripts_fetched += 1

            analysis_text = "\n".join(value for value in (video.title, video.description, transcript) if value)
            analysis = pipeline.process(
                title=video.title,
                text=analysis_text,
                source_url=video.url,
            ).analysis
            story = story_repo.upsert(analysis)
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
    )
