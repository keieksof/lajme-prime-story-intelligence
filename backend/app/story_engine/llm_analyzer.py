from __future__ import annotations

import json
import os
from datetime import datetime
from hashlib import sha256
from typing import Any

from openai import OpenAI

from app.models.domain import StoryAnalysis


SYSTEM_PROMPT = """
You are the Story Intelligence engine for Lajme Prime.
Analyze news text, not just the source headline.
Return structured information that separates facts, allegations, opinions,
rumors, and unverified claims. Preserve uncertainty instead of inventing facts.
Identify the real event, central people and organizations, chronology,
important claims, topics, and the likely canonical story key.
Do not decide virality or write social copy here.
""".strip()


ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "canonical_story_key": {"type": "string"},
        "story_title": {"type": "string"},
        "summary": {"type": "string"},
        "category": {"type": ["string", "null"]},
        "people": {"type": "array", "items": {"type": "string"}},
        "organizations": {"type": "array", "items": {"type": "string"}},
        "topics": {"type": "array", "items": {"type": "string"}},
        "events": {
            "type": "array",
            "items": {"type": "object", "additionalProperties": True},
        },
        "claims": {
            "type": "array",
            "items": {"type": "object", "additionalProperties": True},
        },
        "occurred_at": {"type": ["string", "null"]},
    },
    "required": [
        "canonical_story_key",
        "story_title",
        "summary",
        "category",
        "people",
        "organizations",
        "topics",
        "events",
        "claims",
        "occurred_at",
    ],
}


class LLMStoryAnalyzer:
    def __init__(
        self,
        client: OpenAI | None = None,
        model: str | None = None,
    ) -> None:
        self.client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("STORY_INTELLIGENCE_MODEL", "gpt-5.6-luna")

    def analyze(
        self,
        title: str,
        text: str,
        source_url: str | None = None,
    ) -> StoryAnalysis:
        payload = {
            "title": title,
            "text": text,
            "source_url": source_url,
        }
        response = self.client.responses.create(
            model=self.model,
            instructions=SYSTEM_PROMPT,
            input=json.dumps(payload, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "story_analysis",
                    "strict": True,
                    "schema": ANALYSIS_SCHEMA,
                }
            },
        )
        data = json.loads(response.output_text or "{}")
        return self._to_analysis(data, title=title, text=text)

    @staticmethod
    def _to_analysis(data: dict[str, Any], *, title: str, text: str) -> StoryAnalysis:
        canonical_seed = str(data.get("canonical_story_key") or f"{title}\n{text[:2000]}")
        occurred_at = _parse_datetime(data.get("occurred_at"))
        return StoryAnalysis(
            canonical_key=f"story:{sha256(canonical_seed.lower().strip().encode()).hexdigest()[:24]}",
            title=str(data.get("story_title") or title).strip(),
            summary=str(data.get("summary") or text.strip()[:500]).strip(),
            category=_string_or_none(data.get("category")),
            people=_string_list(data.get("people")),
            organizations=_string_list(data.get("organizations")),
            topics=_string_list(data.get("topics")),
            events=_dict_list(data.get("events")),
            claims=_dict_list(data.get("claims")),
            occurred_at=occurred_at,
        )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
