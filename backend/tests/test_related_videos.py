from datetime import datetime, timezone
from uuid import uuid4

from app.db_models import VideoRow
from app.services.related_videos import rank_related_videos


def _video(title: str, *, story_id=None, published_at=None) -> VideoRow:
    return VideoRow(
        id=uuid4(),
        platform="youtube",
        external_id=str(uuid4()),
        url="https://youtube.com/watch?v=test",
        title=title,
        published_at=published_at or datetime(2026, 9, 10, tzinfo=timezone.utc),
        story_id=story_id,
    )


def test_pgvector_similarity_overrides_lexical_proxy() -> None:
    current = _video("Kuvendi miraton ndryshimet në ligjin e buxhetit")
    low_overlap = _video("Ky vendim ndryshon rregullat për bizneset")
    high_overlap = _video("Ekspertët shpjegojnë efektet e ndryshimit të ligjit të buxhetit")

    ranked = rank_related_videos(
        current,
        [low_overlap, high_overlap],
        limit=2,
        semantic_similarities={low_overlap.id: 0.35, high_overlap.id: 0.94},
    )

    assert ranked[0].video_id == high_overlap.id
    assert ranked[0].features["semantic_similarity"] == 0.94


def test_without_pgvector_data_falls_back_to_lexical_similarity() -> None:
    current = _video("Qeveria prezanton paketën e re fiskale")
    candidate = _video("Qeveria prezanton paketën e re fiskale për bizneset")

    ranked = rank_related_videos(current, [candidate], limit=1)

    assert len(ranked) == 1
    assert 0.0 <= ranked[0].features["semantic_similarity"] <= 1.0
