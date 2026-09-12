from __future__ import annotations

import os

from app.research.models import ResearchReport
from app.research.researcher import OpenAIWebResearcher, Researcher


def build_researcher() -> Researcher:
    provider = os.getenv("RESEARCH_PROVIDER", "openai_web").strip().lower()
    if provider != "openai_web":
        raise ValueError(f"Unsupported RESEARCH_PROVIDER: {provider}")
    return OpenAIWebResearcher()


def research_story(query: str, claims: list[str] | None = None) -> ResearchReport:
    return build_researcher().research(query=query, claims=claims)
