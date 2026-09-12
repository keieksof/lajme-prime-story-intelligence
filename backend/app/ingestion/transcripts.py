from __future__ import annotations

from typing import Any


async def fetch_transcript(video_id: str) -> str | None:
    """Best-effort transcript adapter.

    Transcript retrieval is intentionally optional. A missing transcript must
    never block ingestion of the video metadata.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except ImportError:
        return None

    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        parts: list[str] = []
        for item in transcript:
            if isinstance(item, dict):
                text = item.get("text")
            else:
                text = getattr(item, "text", None)
            if text:
                parts.append(str(text).strip())
        return " ".join(parts).strip() or None
    except Exception:
        return None
