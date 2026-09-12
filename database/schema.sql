-- Lajme Prime Story Intelligence Engine
-- Initial relational schema. PostgreSQL + pgvector compatible.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_key TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    category TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    first_seen_at TIMESTAMPTZ,
    last_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    occurred_at TIMESTAMPTZ,
    source_url TEXT,
    confidence NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID REFERENCES stories(id) ON DELETE SET NULL,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    claim_text TEXT NOT NULL,
    claim_type TEXT NOT NULL DEFAULT 'claim',
    verification_status TEXT NOT NULL DEFAULT 'unverified',
    confidence NUMERIC(5,4),
    source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,
    external_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    published_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    transcript TEXT,
    story_id UUID REFERENCES stories(id) ON DELETE SET NULL,
    embedding vector(1536),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(platform, external_id)
);

CREATE TABLE IF NOT EXISTS story_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    to_story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    strength NUMERIC(6,4),
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(from_story_id, to_story_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS video_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    current_video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    candidate_video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    score NUMERIC(8,4) NOT NULL,
    ranking_features JSONB NOT NULL DEFAULT '{}'::jsonb,
    llm_judgement JSONB NOT NULL DEFAULT '{}'::jsonb,
    selected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(current_video_id, candidate_video_id)
);

CREATE TABLE IF NOT EXISTS publications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    external_url TEXT,
    published_at TIMESTAMPTZ,
    related_video_id UUID REFERENCES videos(id) ON DELETE SET NULL,
    editorial_version TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publication_id UUID NOT NULL REFERENCES publications(id) ON DELETE CASCADE,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    views BIGINT,
    likes BIGINT,
    comments BIGINT,
    shares BIGINT,
    impressions BIGINT,
    ctr NUMERIC(8,5),
    average_view_duration_seconds NUMERIC(12,4),
    average_percentage_viewed NUMERIC(8,5),
    swipe_away_rate NUMERIC(8,5),
    retention JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_metrics JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS learning_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publication_id UUID REFERENCES publications(id) ON DELETE SET NULL,
    signal_type TEXT NOT NULL,
    feature_key TEXT NOT NULL,
    feature_value JSONB,
    outcome_value NUMERIC,
    confidence NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_story_time ON events(story_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_claims_story ON claims(story_id);
CREATE INDEX IF NOT EXISTS idx_videos_story ON videos(story_id);
CREATE INDEX IF NOT EXISTS idx_videos_published_at ON videos(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_story_relationships_from ON story_relationships(from_story_id);
CREATE INDEX IF NOT EXISTS idx_story_relationships_to ON story_relationships(to_story_id);
CREATE INDEX IF NOT EXISTS idx_video_relationships_current ON video_relationships(current_video_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_performance_publication_time ON performance_metrics(publication_id, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_learning_feature ON learning_signals(feature_key, created_at DESC);

-- Vector index can be added after the first meaningful corpus exists.
-- CREATE INDEX idx_videos_embedding ON videos USING hnsw (embedding vector_cosine_ops);
