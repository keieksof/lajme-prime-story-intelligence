from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.domain import StoryAnalysis


@dataclass(frozen=True)
class StoryMatch:
    relationship_type: str
    score: float
    reasons: list[str]


def match_stories(current: StoryAnalysis, candidate: StoryAnalysis) -> StoryMatch:
    people = _overlap(current.people, candidate.people)
    organizations = _overlap(current.organizations, candidate.organizations)
    topics = _overlap(current.topics, candidate.topics)
    titles = _token_overlap(current.title, candidate.title)

    score = (
        people * 0.35
        + organizations * 0.15
        + topics * 0.20
        + titles * 0.15
        + (0.15 if current.canonical_key == candidate.canonical_key else 0.0)
    )

    reasons: list[str] = []
    if current.canonical_key == candidate.canonical_key:
        reasons.append("same canonical story key")
    if people:
        reasons.append(f"shared people: {people:.2f}")
    if organizations:
        reasons.append(f"shared organizations: {organizations:.2f}")
    if topics:
        reasons.append(f"shared topics: {topics:.2f}")
    if titles:
        reasons.append(f"title overlap: {titles:.2f}")

    if score >= 0.75:
        relation = "SAME_STORY"
    elif people >= 0.75 and topics >= 0.35:
        relation = "SAME_PERSON_NEW_DEVELOPMENT"
    elif people >= 0.50:
        relation = "REACTION_CHAIN"
    elif topics >= 0.70:
        relation = "SAME_TOPIC_NOT_SAME_STORY"
    else:
        relation = "CONTEXT_ONLY"

    return StoryMatch(
        relationship_type=relation,
        score=round(score, 4),
        reasons=reasons,
    )


def _overlap(left: list[str], right: list[str]) -> float:
    if not left or not right:
        return 0.0
    a = {item.casefold().strip() for item in left if item.strip()}
    b = {item.casefold().strip() for item in right if item.strip()}
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _token_overlap(left: str, right: str) -> float:
    a = _tokens(left)
    b = _tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _tokens(value: str) -> set[str]:
    stop = {
        "eshte", "është", "dhe", "per", "për", "nga", "me", "kete", "këtë",
        "nje", "një", "the", "this", "that", "news", "lajme",
    }
    return {
        token
        for token in re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", value.casefold())
        if token not in stop
    }
