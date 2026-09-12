from app.models.domain import StoryAnalysis
from app.story_engine.story_matcher import match_stories


def make_story(
    key: str,
    title: str,
    people: list[str],
    topics: list[str],
) -> StoryAnalysis:
    return StoryAnalysis(
        canonical_key=key,
        title=title,
        summary=title,
        people=people,
        topics=topics,
    )


def test_same_canonical_key_is_same_story() -> None:
    current = make_story("story:abc", "Berisha reagon për protestën", ["Sali Berisha"], ["protesta"])
    candidate = make_story("story:abc", "Berisha flet pas protestës", ["Sali Berisha"], ["protesta"])

    match = match_stories(current, candidate)

    assert match.relationship_type == "SAME_STORY"
    assert match.score >= 0.75


def test_same_person_and_topic_can_be_new_development() -> None:
    current = make_story("story:one", "Berisha njofton protestën", ["Sali Berisha"], ["protesta"])
    candidate = make_story("story:two", "Berisha komenton protestën", ["Sali Berisha"], ["protesta"])

    match = match_stories(current, candidate)

    assert match.relationship_type in {"SAME_PERSON_NEW_DEVELOPMENT", "REACTION_CHAIN", "SAME_STORY"}
    assert match.score > 0


def test_unrelated_topics_are_not_same_story() -> None:
    current = make_story("story:one", "Moti në Tiranë", [], ["moti", "Tiranë"])
    candidate = make_story("story:two", "Finalja e futbollit", [], ["futboll", "sport"])

    match = match_stories(current, candidate)

    assert match.relationship_type == "CONTEXT_ONLY"
