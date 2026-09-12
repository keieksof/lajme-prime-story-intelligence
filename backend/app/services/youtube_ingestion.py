from __future__ import annotations

from dataclasses import dataclass

from app.db import SessionLocal
from app.ingestion.youtube import YouTubeClient
from app.repositories.story_repository import StoryRepository
from app.repositories.youtube_repository import YouTubeRepository
from app.story_engine.analyzer import HeuristicStoryAnalyzer
from app.story_engine.pipeline import StoryIntelligencePipeline


@dataclass(frozen=True)
class IngestionResult:
    imported: int
    updated: int


async def ingest_channel(api_key: str, channel: str, limit: int = 50) -> IngestionResult:
    client = YouTubeClient(api_key=api_key)
    videos = await client.list_uploads(channel, limit=limit)
    pipeline = StoryIntelligencePipeline(HeuristicStoryAnalyzer())

    imported = 0
    updated = 0

    with SessionLocal() as session:
        video_repo = YouTubeRepository(session)
        story_repo = StoryRepository(session)

        for video in videos:
            analysis = pipeline.process(
                title=video.title,
                text=f"{video.title}\n{video.description}",
                source_url=video.url,
            ).analysis
            story = story_repo.upsert(analysis)
            existing = next(
                (
                    row
                    for row in video_repo.list_recent(limit=max(limit, 100))
                    if row.platform == "youtube" and row.external_id == video.external_id
                ),
                None,
            )
            video_repo.upsert_video(video, story_id=str(story.id))
            if existing is None:
                imported += 1
            else:
                updated += 1

        session.commit()

    return IngestionResult(imported=imported, updated=updated)
