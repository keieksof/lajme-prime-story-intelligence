# Lajme Prime Story Intelligence

AI-powered editorial intelligence system for Lajme Prime.

## Vision

The system builds a persistent understanding of Lajme Prime's stories and published videos. For every new story it should:

- fact-check and structure the story
- identify the story and its historical context
- connect the story to previous developments
- find and rank genuinely related YouTube videos
- generate editorial outputs
- learn from performance after publication

## Core loop

`New story -> Story Intelligence -> Story Graph -> Related Video Ranking -> Publish -> Performance Data -> Learning -> Better next decision`

## Initial architecture

- Backend: Python / FastAPI
- Database: PostgreSQL + pgvector
- LLM layer: provider-agnostic interface, initially designed for OpenAI
- Retrieval: semantic + structured retrieval
- Story graph: PostgreSQL relationships first, graph database optional later
- Learning: feedback signals and ranking model, without changing the base LLM after every upload

## Principles

1. Factuality before virality.
2. A related video must have an editorial relationship, not merely similar keywords.
3. Story history is persistent and chronological.
4. Every publication can produce learning signals.
5. Human review remains possible at every important decision point.
6. Never fabricate performance metrics or factual claims.
