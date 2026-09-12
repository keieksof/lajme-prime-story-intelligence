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

## Current build

The repository now contains:

- FastAPI backend
- PostgreSQL + pgvector schema
- SQLAlchemy persistence models and repositories
- YouTube channel ingestion through the YouTube Data API
- YouTube transcript fetching when available
- Story analysis pipeline
- Explainable Related Video baseline ranker
- Learning feedback baseline
- GitHub Actions CI
- Docker Compose PostgreSQL/pgvector development stack

## Local development

1. Copy `.env.example` to `.env` and set `YOUTUBE_API_KEY`.
2. Start PostgreSQL:

```bash
docker compose up -d postgres
```

3. Install backend dependencies:

```bash
cd backend
python -m pip install -r requirements.txt
```

4. Start the API:

```bash
PYTHONPATH=. uvicorn app.main:app --reload
```

5. Ingest the latest Lajme Prime uploads:

```bash
curl -X POST "http://localhost:8000/api/youtube/ingest?channel=@LajmePrime&limit=25"
```

## Architecture

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
