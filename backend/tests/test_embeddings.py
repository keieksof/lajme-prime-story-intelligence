from __future__ import annotations

from types import SimpleNamespace

from app.services.embeddings import OpenAIEmbeddingService, video_embedding_text
from app.services.related_videos import cosine_similarity


def test_cosine_similarity_is_normalized() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([1.0], [1.0, 1.0]) == 0.0


def test_video_embedding_text_includes_available_fields() -> None:
    video = SimpleNamespace(
        title="Titull",
        description="Përshkrim",
        transcript="Transkript",
    )
    assert video_embedding_text(video) == "Titull\n\nPërshkrim\n\nTranskript"


def test_embedding_service_sorts_response_by_index() -> None:
    class FakeEmbeddings:
        def create(self, **_: object) -> object:
            return SimpleNamespace(
                data=[
                    SimpleNamespace(index=1, embedding=[0.2, 0.3]),
                    SimpleNamespace(index=0, embedding=[0.1, 0.4]),
                ]
            )

    service = OpenAIEmbeddingService.__new__(OpenAIEmbeddingService)
    service.client = SimpleNamespace(embeddings=FakeEmbeddings())
    service.model = "test-model"

    assert service.embed_texts(["a", "b"]) == [[0.1, 0.4], [0.2, 0.3]]
