from __future__ import annotations

import json
import os
from typing import Any, Protocol

from app.research.models import FactCheckFinding, ResearchReport, ResearchSource


class Researcher(Protocol):
    def research(self, query: str, claims: list[str] | None = None) -> ResearchReport:
        ...


class OpenAIWebResearcher:
    """Web research + fact-check adapter using the Responses API web_search tool.

    The researcher is intentionally separated from Story Intelligence so source
    discovery and factual verification can evolve without changing the story
    extraction pipeline.
    """

    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("STORY_RESEARCH_MODEL", "gpt-5.6-luna")

    def research(self, query: str, claims: list[str] | None = None) -> ResearchReport:
        claim_text = "\n".join(f"- {claim}" for claim in (claims or [])) or "No explicit claims supplied."
        prompt = f"""
Research the following news story and fact-check the supplied claims.

STORY / QUERY:
{query}

CLAIMS:
{claim_text}

Rules:
1. Search the web. Prefer primary sources, official statements, court documents,
   government data, and established news organizations.
2. Separate verified facts from allegations, opinions, rumors, and unresolved claims.
3. Reconstruct the key chronology when earlier developments are necessary.
4. Never invent a source, quote, date, number, or event.
5. For every finding, provide a verdict of one of: confirmed, mostly_confirmed,
   disputed, unconfirmed, false, or opinion.
6. Be explicit about limitations when evidence is incomplete or conflicting.

Return JSON only with keys:
summary, timeline, findings, sources, limitations.
Each source must contain title, url, publisher, published_at.
Each finding must contain claim, verdict, confidence, explanation, sources.
"""

        response = self.client.responses.create(
            model=self.model,
            tools=[{"type": "web_search"}],
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "fact_check_report",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "summary": {"type": "string"},
                            "timeline": {"type": "array", "items": {"type": "string"}},
                            "findings": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "claim": {"type": "string"},
                                        "verdict": {"type": "string"},
                                        "confidence": {"type": "number"},
                                        "explanation": {"type": "string"},
                                        "sources": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": False,
                                                "properties": {
                                                    "title": {"type": "string"},
                                                    "url": {"type": "string"},
                                                    "publisher": {"type": ["string", "null"]},
                                                    "published_at": {"type": ["string", "null"]},
                                                },
                                                "required": ["title", "url", "publisher", "published_at"],
                                            },
                                        },
                                    },
                                    "required": [
                                        "claim",
                                        "verdict",
                                        "confidence",
                                        "explanation",
                                        "sources",
                                    ],
                                },
                            },
                            "sources": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "title": {"type": "string"},
                                        "url": {"type": "string"},
                                        "publisher": {"type": ["string", "null"]},
                                        "published_at": {"type": ["string", "null"]},
                                    },
                                    "required": ["title", "url", "publisher", "published_at"],
                                },
                            },
                            "limitations": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["summary", "timeline", "findings", "sources", "limitations"],
                    },
                }
            },
        )

        payload: dict[str, Any] = json.loads(response.output_text)
        return _report_from_payload(query, payload)


def _source_from_payload(value: dict[str, Any]) -> ResearchSource:
    return ResearchSource(
        title=str(value.get("title", "")),
        url=str(value.get("url", "")),
        publisher=value.get("publisher"),
        published_at=value.get("published_at"),
    )


def _report_from_payload(query: str, payload: dict[str, Any]) -> ResearchReport:
    findings: list[FactCheckFinding] = []
    for item in payload.get("findings", []):
        findings.append(
            FactCheckFinding(
                claim=str(item.get("claim", "")),
                verdict=str(item.get("verdict", "unconfirmed")),
                confidence=float(item.get("confidence", 0.0)),
                explanation=str(item.get("explanation", "")),
                sources=[_source_from_payload(source) for source in item.get("sources", [])],
            )
        )

    return ResearchReport(
        query=query,
        summary=str(payload.get("summary", "")),
        timeline=[str(item) for item in payload.get("timeline", [])],
        findings=findings,
        sources=[_source_from_payload(source) for source in payload.get("sources", [])],
        limitations=[str(item) for item in payload.get("limitations", [])],
    )
