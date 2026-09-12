from datetime import datetime, timezone

from app.story_engine.graph import StoryNode, build_edges


def test_previous_development_is_ranked_first() -> None:
    current = StoryNode(
        video_id="current",
        story_id="story-1",
        title="Update",
        published_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        people=frozenset({"person-a"}),
        topics=frozenset({"topic-a"}),
    )
    previous = StoryNode(
        video_id="previous",
        story_id="story-1",
        title="Earlier",
        published_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
        people=frozenset({"person-a"}),
        topics=frozenset({"topic-a"}),
    )

    edges = build_edges(current, [previous])

    assert edges[0].relationship_type == "PREVIOUS_DEVELOPMENT"
    assert edges[0].confidence == 0.95
