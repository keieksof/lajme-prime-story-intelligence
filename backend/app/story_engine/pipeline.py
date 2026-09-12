from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any

from app.research.models import ResearchReport
from app.research.service import build_researcher
from app.story_engine.analyzer import StoryAnalyzer, analysis_to_dict


@dataclass
class IngestedStory:
    analysis: dict[str, Any]
    source_url: str | None = None
    research: dict[str, Any] | None = None


class StoryIntelligencePipeline:
    def __init__(
        self,
        analyzer: StoryAnalyzer,
        researcher: Any | None = None,
        research_enabled: bool | None = None,
    ) -> None:
        self.analyzer = analyzer
        self.researcher = researcher
        self.research_enabled = (
            research_enabled
            if research_enabled is not None
            else os.getenv("RESEARCH_ENABLED", "false").strip().lower() in {"1", "true", "yes"}
        )

    def process(self, title: str, text: str, source_url: str | None = None) -> IngestedStory:
        if not title.strip():
            raise ValueError("title must not be empty")
        if not text.strip():
            raise ValueError("text must not be empty")

        story = self.analyzer.analyze(title=title, text=text, source_url=source_url)
        analysis = analysis_to_dict(story)
        research: dict[str, Any] | None = None

        if self.research_enabled:
            researcher = self.researcher or build_researcher()
            claims = _claims_for_research(story.claims)
            query = _research_query(story.title, story.summary, story.people, story.organizations)
            report = researcher.research(query=query, claims=claims)
            research = asdict(report)

        return IngestedStory(
            analysis=analysis,
            source_url=source_url,
            research=research,
        )


def _research_query(
    title: str,
    summary: str,
    people: list[str],
    organizations: list[str],
) -> str:
    entities = ", ".join(dict.fromkeys([*people, *organizations]))
    parts = [title.strip(), summary.strip()]
    if entities:
        parts.append(f"Entities: {entities}")
    return "\n".join(part for part in parts if part)


def _claims_for_research(claims: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for claim in claims:
        value = claim.get("claim") or claim.get("text") or claim.get("statement")
        if value is not None and str(value).strip():
            result.append(str(value).strip())
    return result


def serialize_research(report: ResearchReport | None) -> dict[str, Any] | None:
    return asdict(report) if report is not None else None
