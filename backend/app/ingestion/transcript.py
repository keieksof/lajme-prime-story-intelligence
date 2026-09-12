from __future__ import annotations

from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptFetcher:
    def fetch(self, video_id: str) -> str | None:
        try:
            transcript = YouTubeTranscriptApi().fetch(video_id)
        except Exception:
            return None
        return " ".join(snippet.text for snippet in transcript).strip() or None
