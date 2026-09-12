# Architecture

## Goal

Create a persistent Story Intelligence Engine for Lajme Prime that understands each story, its history, related published content, and the performance feedback generated after publication.

## Pipeline

1. Ingest source article or URL.
2. Retrieve and fact-check relevant external information.
3. Extract entities, events, claims, dates, locations, topics, and chronology.
4. Resolve the story into an existing Story ID or create a new story.
5. Build or update chronological story relationships.
6. Retrieve candidate previous videos using structured and semantic signals.
7. Rank candidates using relationship-aware scoring.
8. Use an LLM judge to validate the strongest candidate and relationship type.
9. Generate editorial outputs.
10. Store the published content and selected related video.
11. Ingest post-publication performance signals.
12. Update learning statistics and ranking features.

## Related-video relationship types

- SAME_STORY
- SAME_PERSON_NEW_DEVELOPMENT
- REACTION_CHAIN
- PREVIOUS_DEVELOPMENT
- FOLLOW_UP
- SAME_TOPIC_NOT_SAME_STORY
- CONTEXT_ONLY

The system must not recommend a video solely because it shares keywords with the current story.

## Learning architecture

The base LLM is not retrained after every upload. Instead, the system stores structured feedback and learns through retrieval, feature weights, ranking statistics, and editorial rules derived from observed outcomes.

Future versions may add a learned ranking model once enough historical data exists.
