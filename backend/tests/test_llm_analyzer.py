from app.story_engine.llm_analyzer import LLMStoryAnalyzer


def test_llm_payload_is_normalized_to_story_analysis() -> None:
    analysis = LLMStoryAnalyzer._to_analysis(
        {
            "canonical_story_key": "berisha-protest-response",
            "story_title": "Berisha reagon për protestën",
            "summary": "Berisha reagoi pas protestës.",
            "category": "politics",
            "people": ["Sali Berisha"],
            "organizations": ["Partia Demokratike"],
            "topics": ["protesta", "politikë"],
            "events": [{"title": "Reagimi pas protestës", "type": "reaction"}],
            "claims": [
                {
                    "claim": "Berisha tha se protesta do të vijojë.",
                    "claim_type": "statement",
                    "verification_status": "reported",
                }
            ],
            "occurred_at": "2026-09-12T10:00:00+02:00",
        },
        title="Titull fallback",
        text="Tekst fallback",
    )

    assert analysis.title == "Berisha reagon për protestën"
    assert analysis.people == ["Sali Berisha"]
    assert analysis.organizations == ["Partia Demokratike"]
    assert analysis.claims[0]["verification_status"] == "reported"
    assert analysis.occurred_at is not None
