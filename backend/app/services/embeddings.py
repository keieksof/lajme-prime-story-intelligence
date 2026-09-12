from __future__ import annotations

import os
from collections.abc import Iterable, Sequence

from openai import OpenAI
from sqlalchemy.orm import Session

from app.db_models import VideoRow

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


def video_embedding_text(video: VideoRow) -> str:
    parts = [video.title.strip()]
    if video.description:
        parts.append(video.description.strip())
    if video.transcript:
        parts.append(video.transcript.strip())
    return "\n\n".join(part for part in parts if part)


class OpenAIEmbeddingService:
    def __init__(
        self,
        client: OpenAI | None = None,
        model: str | None = None,
    ) -> None:
        self.client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(
            model=self.model,
            input=list(texts),
            dimensions=EMBEDDING_DIMENSION,
        )
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]

    def embed_videos(self, videos: Sequence[VideoRow], *, batch_size: int = 100) -> int:
        updated = 0
        for start in range(0, len(videos), batch_size):
            batch = list(videos[start : start + batch_size])
            texts = [video_embedding_text(video) for video in batch]
            embeddings = self.embed_texts(texts)
            for video, embedding in zip(batch, embeddings, strict=True):
                video.embedding = embedding
                updated += 1
        return updated


def embed_missing_videos(
    session: Session,
    videos: Iterable[VideoRow],
    service: OpenAIEmbeddingService | None = None,
    *,
    batch_size: int = 100,
) -> int:
    pending = [video for video in videos if video.embedding is None and video_embedding_text(video)]
    if not pending:
        return 0
    embedding_service = service or OpenAIEmbeddingService()
    updated = embedding_service.embed_videos(pending, batch_size=batch_size)
    session.flush()
    return updated
