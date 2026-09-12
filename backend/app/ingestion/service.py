from __future__ import annotations

from app.core.settings import settings
from app.ingestion.transcripts import fetch_transcript
from app.ingestion.youtube import YouTubeClient


async def ingest_youtube_channel(channel: str, limit: int = 25) -> list[dict]:
    if not settings.youtube_api_key:
        raise RuntimeError("YOUTUBE_API_KEY is not configured")

    client = YouTubeClient(settings.youtube_api_key)
    videos = await client.list_uploads(channel, limit=limit)
    results: list[dict] = []
    for video in videos:
        transcript = await fetch_transcript(video.external_id)
        results.append(
            {
                "external_id": video.external_id,
                "url": video.url,
                "title": video.title,
                "description": video.description,
                "published_at": video.published_at.isoformat() if video.published_at else None,
                "duration_seconds": video.duration_seconds,
                "channel_id": video.channel_id,
                "transcript": transcript,
                "raw": video.raw,
            }
        )
    return results
