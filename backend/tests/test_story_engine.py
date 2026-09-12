from app.story_engine.analyzer import HeuristicStoryAnalyzer
from app.story_engine.pipeline import StoryIntelligencePipeline


def test_story_key_is_deterministic() -> None:
    analyzer = HeuristicStoryAnalyzer()
    a = analyzer.analyze("Titull", "Tekst i lajmit.")
    b = analyzer.analyze("Titull", "Tekst i lajmit.")
    assert a.canonical_key == b.canonical_key


def test_pipeline_rejects_empty_input() -> None:
    pipeline = StoryIntelligencePipeline(HeuristicStoryAnalyzer())
    try:
        pipeline.process("", "Tekst")
    except ValueError as exc:
        assert "title" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_pipeline_returns_structured_story() -> None:
    pipeline = StoryIntelligencePipeline(HeuristicStoryAnalyzer())
    result = pipeline.process(
        "Rama flet për programin e banesave",
        "Programi pritet të sjellë kredi të buta për familjet.",
        "https://example.com/news",
    )
    assert result.analysis["canonical_key"].startswith("story:")
    assert result.analysis["title"] == "Rama flet për programin e banesave"
    assert result.source_url == "https://example.com/news"
