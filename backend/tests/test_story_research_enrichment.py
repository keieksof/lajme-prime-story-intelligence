from app.models.domain import StoryAnalysis
from app.research.models import ResearchReport
from app.story_engine.analyzer import HeuristicStoryAnalyzer
from app.story_engine.pipeline import StoryIntelligencePipeline, _claims_for_research, _research_query


class FakeResearcher:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def research(self, query: str, claims: list[str] | None = None) -> ResearchReport:
        normalized_claims = claims or []
        self.calls.append((query, normalized_claims))
        return ResearchReport(
            query=query,
            summary="Verified context.",
            timeline=["Event A"],
            limitations=["Test limitation"],
        )


def test_research_helpers_extract_claims_and_entities() -> None:
    assert _claims_for_research(
        [{"claim": "Claim A"}, {"text": "Claim B"}, {"statement": "Claim C"}]
    ) == ["Claim A", "Claim B", "Claim C"]
    query = _research_query("Titulli", "Permbledhja", ["Person A"], ["Org A"])
    assert "Person A, Org A" in query


def test_pipeline_can_optionally_enrich_story_with_research() -> None:
    researcher = FakeResearcher()
    pipeline = StoryIntelligencePipeline(
        HeuristicStoryAnalyzer(),
        researcher=researcher,
        research_enabled=True,
    )

    result = pipeline.process("Titull lajmi", "Teksti i lajmit.")

    assert result.research is not None
    assert result.research["summary"] == "Verified context."
    assert researcher.calls


def test_pipeline_does_not_research_by_default() -> None:
    researcher = FakeResearcher()
    pipeline = StoryIntelligencePipeline(
        HeuristicStoryAnalyzer(),
        researcher=researcher,
        research_enabled=False,
    )

    result = pipeline.process("Titull lajmi", "Teksti i lajmit.")

    assert result.research is None
    assert researcher.calls == []
