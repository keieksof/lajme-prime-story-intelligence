from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from datetime import datetime
from typing import Protocol

from app.models.domain import StoryAnalysis


class StoryAnalyzer(Protocol):
    def analyze(self, title: str, text: str, source_url: str | None = None) -> StoryAnalysis:
        ...


class HeuristicStoryAnalyzer:
    """Deterministic fallback analyzer used before the LLM extractor is wired in.

    It creates a stable story key from normalized title/text and deliberately
    does not pretend to verify factual claims. LLM + source verification are
    separate stages in the production pipeline.
    """

    def analyze(self, title: str, text: str, source_url: str | None = None) -> StoryAnalysis:
        normalized = self._normalize(f"{title}\n{text}")
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
        summary = self._first_sentence(text) or title.strip()
        return StoryAnalysis(
            canonical_key=f"story:{digest}",
            title=title.strip(),
            summary=summary,
            category=None,
            people=[],
            organizations=[],
            topics=self._keywords(normalized),
            events=[],
            claims=[],
            occurred_at=None,
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value.lower()).strip()

    @staticmethod
    def _first_sentence(value: str) -> str:
        parts = re.split(r"(?<=[.!?])\s+", value.strip(), maxsplit=1)
        return parts[0][:500] if parts else ""

    @staticmethod
    def _keywords(value: str) -> list[str]:
        words = re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", value)
        stop = {
            "eshte", "është", "dhe", "per", "për", "nga", "me", "kete", "këtë",
            "nje", "një", "the", "this", "that", "have", "with", "from",
        }
        seen: list[str] = []
        for word in words:
            if word in stop or word in seen:
                continue
            seen.append(word)
            if len(seen) >= 12:
                break
        return seen


def analysis_to_dict(analysis: StoryAnalysis) -> dict:
    result = asdict(analysis)
    if isinstance(result.get("occurred_at"), datetime):
        result["occurred_at"] = result["occurred_at"].isoformat()
    return result
