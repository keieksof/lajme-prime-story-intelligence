from app.research.models import ResearchReport
from app.research.researcher import _report_from_payload


def test_report_normalization_preserves_fact_check_verdicts() -> None:
    report = _report_from_payload(
        "test query",
        {
            "summary": "Verified summary.",
            "timeline": ["Event A", "Event B"],
            "findings": [
                {
                    "claim": "Claim A",
                    "verdict": "confirmed",
                    "confidence": 0.93,
                    "explanation": "Supported by primary evidence.",
                    "sources": [
                        {
                            "title": "Official statement",
                            "url": "https://example.com/official",
                            "publisher": "Example Gov",
                            "published_at": "2026-09-12",
                        }
                    ],
                }
            ],
            "sources": [
                {
                    "title": "Official statement",
                    "url": "https://example.com/official",
                    "publisher": "Example Gov",
                    "published_at": "2026-09-12",
                }
            ],
            "limitations": ["Only one primary source available."],
        },
    )

    assert isinstance(report, ResearchReport)
    assert report.query == "test query"
    assert report.findings[0].verdict == "confirmed"
    assert report.findings[0].confidence == 0.93
    assert report.sources[0].url == "https://example.com/official"
    assert report.limitations
