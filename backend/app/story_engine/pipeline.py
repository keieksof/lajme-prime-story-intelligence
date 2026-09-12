from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.story_engine.analyzer import StoryAnalyzer, analysis_to_dict


@dataclass
class IngestedStory:
    analysis: dict[str, Any]
    source_url: str | None = None


class StoryIntelligencePipeline:
    def __init__(self, analyzer: StoryAnalyzer) -> None:
        self.analyzer = analyzer

    def process(self, title: str, text: str, source_url: str | None = None) -> IngestedStory:
        if not title.strip():
            raise ValueError("title must not be empty")
        if not text.strip():
            raise ValueError("text must not be empty")

        analysis = self.analyzer.analyze(title=title, text=text, source_url=source_url)
        return IngestedStory(
            analysis=analysis_to_dict(analysis),
            source_url=source_url,
        )
