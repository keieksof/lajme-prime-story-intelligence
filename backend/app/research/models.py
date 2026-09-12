from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResearchSource:
    title: str
    url: str
    publisher: str | None = None
    published_at: str | None = None


@dataclass(frozen=True)
class FactCheckFinding:
    claim: str
    verdict: str
    confidence: float
    explanation: str
    sources: list[ResearchSource] = field(default_factory=list)


@dataclass(frozen=True)
class ResearchReport:
    query: str
    summary: str
    timeline: list[str] = field(default_factory=list)
    findings: list[FactCheckFinding] = field(default_factory=list)
    sources: list[ResearchSource] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
