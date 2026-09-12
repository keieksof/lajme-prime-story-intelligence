from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx


YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


@dataclass(frozen=True)
class YouTubeVideo:
    external_id: str
    url: str
    title: str
    description: str
    published_at: datetime | None
    duration_seconds: int | None
    channel_id: str
    raw: dict[str, Any]


def _iso_duration_to_seconds(value: str | None) -> int | None:
    if not value or not value.startswith("PT"):
        return None
    seconds = 0
    number = ""
    for char in value[2:]:
        if char.isdigit():
            number += char
            continue
        if not number:
            continue
        n = int(number)
        number = ""
        if char == "H":
            seconds += n * 3600
        elif char == "M":
            seconds += n * 60
        elif char == "S":
            seconds += n
    return seconds


class YouTubeClient:
    def __init__(self, api_key: str, timeout: float = 20.0) -> None:
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY is required")
        self.api_key = api_key
        self.timeout = timeout

    async def resolve_channel(self, handle_or_id: str) -> dict[str, Any]:
        value = handle_or_id.strip()
        params = {"part": "id,snippet,contentDetails", "key": self.api_key}
        if value.startswith("UC"):
            params["id"] = value
        else:
            params["forHandle"] = value.removeprefix("@")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{YOUTUBE_API_BASE}/channels", params=params)
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                raise LookupError(f"YouTube channel not found: {handle_or_id}")
            return items[0]

    async def list_uploads(self, channel_id: str, limit: int = 50) -> list[YouTubeVideo]:
        channel = await self.resolve_channel(channel_id)
        uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids: list[str] = []
        next_page: str | None = None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while len(video_ids) < limit:
                params = {
                    "part": "contentDetails",
                    "playlistId": uploads_playlist,
                    "maxResults": min(50, limit - len(video_ids)),
                    "key": self.api_key,
                }
                if next_page:
                    params["pageToken"] = next_page
                response = await client.get(f"{YOUTUBE_API_BASE}/playlistItems", params=params)
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("items", []):
                    video_id = item.get("contentDetails", {}).get("videoId")
                    if video_id:
                        video_ids.append(video_id)
                next_page = payload.get("nextPageToken")
                if not next_page:
                    break

            videos: list[YouTubeVideo] = []
            for start in range(0, len(video_ids), 50):
                chunk = video_ids[start:start + 50]
                params = {
                    "part": "snippet,contentDetails,statistics",
                    "id": ",".join(chunk),
                    "key": self.api_key,
                }
                response = await client.get(f"{YOUTUBE_API_BASE}/videos", params=params)
                response.raise_for_status()
                for item in response.json().get("items", []):
                    snippet = item.get("snippet", {})
                    published = snippet.get("publishedAt")
                    published_at = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else None
                    videos.append(
                        YouTubeVideo(
                            external_id=item["id"],
                            url=f"https://www.youtube.com/watch?v={item['id']}",
                            title=snippet.get("title", "").strip(),
                            description=snippet.get("description", "").strip(),
                            published_at=published_at,
                            duration_seconds=_iso_duration_to_seconds(item.get("contentDetails", {}).get("duration")),
                            channel_id=snippet.get("channelId", channel_id),
                            raw=item,
                        )
                    )
        videos.sort(key=lambda video: video.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return videos[:limit]
