from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateSignals:
    same_story: float = 0.0
    same_person: float = 0.0
    same_event: float = 0.0
    chronological_continuity: float = 0.0
    reaction_chain: float = 0.0
    semantic_similarity: float = 0.0
    same_topic_only: float = 0.0


RELATION_WEIGHTS = {
    "same_story": 40.0,
    "same_person": 20.0,
    "same_event": 20.0,
    "chronological_continuity": 20.0,
    "reaction_chain": 15.0,
    "semantic_similarity": 10.0,
    "same_topic_only": 5.0,
}


def score_candidate(signals: CandidateSignals) -> float:
    """Return an explainable baseline score for a related-video candidate.

    Values are normalized to 0..1. The score intentionally rewards editorial
    relationships more strongly than generic semantic similarity.
    """
    values = {
        "same_story": signals.same_story,
        "same_person": signals.same_person,
        "same_event": signals.same_event,
        "chronological_continuity": signals.chronological_continuity,
        "reaction_chain": signals.reaction_chain,
        "semantic_similarity": signals.semantic_similarity,
        "same_topic_only": signals.same_topic_only,
    }
    return sum(RELATION_WEIGHTS[key] * max(0.0, min(1.0, value)) for key, value in values.items())


def classify_relationship(signals: CandidateSignals) -> str:
    if signals.same_story >= 0.8 and signals.chronological_continuity >= 0.5:
        return "PREVIOUS_DEVELOPMENT"
    if signals.same_story >= 0.8:
        return "SAME_STORY"
    if signals.reaction_chain >= 0.7:
        return "REACTION_CHAIN"
    if signals.same_person >= 0.8 and signals.same_event < 0.5:
        return "SAME_PERSON_NEW_DEVELOPMENT"
    if signals.same_topic_only >= 0.7:
        return "SAME_TOPIC_NOT_SAME_STORY"
    return "CONTEXT_ONLY"
