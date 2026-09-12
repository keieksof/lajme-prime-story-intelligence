from app.models.domain import StoryAnalysis
from app.story_engine.story_resolution import choose_best_match


def make_story(key: str, title: str, people: list[str], topics: list[str]) -> StoryAnalysis:
    return StoryAnalysis(
        canonical_key=key,
        title=title,
        summary=title,
        people=people,
        topics=topics,
    )


def test_choose_best_match_prefers_same_story() -> None:
    current = make_story(
        "story:new",
        "Berisha reagon për protestën",
        ["Sali Berisha"],
        ["protesta", "politikë"],
    )
    same_story = make_story(
        "story:old",
        "Berisha flet pas protestës",
        ["Sali Berisha"],
        ["protesta", "politikë"],
    )
    unrelated = make_story(
        "story:other",
        "Rama prezanton projektin",
        ["Edi Rama"],
        ["ekonomi"],
    )

    result = choose_best_match(current, [unrelated, same_story])

    assert result is not None
    assert result[0].canonical_key == "story:old"
    assert result[1].relationship_type in {"SAME_STORY", "SAME_PERSON_NEW_DEVELOPMENT"}


def test_choose_best_match_returns_none_without_candidates() -> None:
    current = make_story("story:new", "Titull", [], ["topic"])

    assert choose_best_match(current, []) is None
