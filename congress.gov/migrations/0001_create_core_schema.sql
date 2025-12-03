-- 0001_create_core_schema.sql
--
-- Establishes the `congress` schema plus foundational lookup tables shared across
-- every Congress.gov resource. Designed for PostgreSQL 14+.

BEGIN;

CREATE SCHEMA IF NOT EXISTS congress;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS congress.sessions (
    congress_number      integer PRIMARY KEY,
    start_date           date NOT NULL,
    end_date             date,
    odd_year             integer NOT NULL,
    even_year            integer NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.chambers (
    chamber_code         text PRIMARY KEY,
    name                 text NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

INSERT INTO congress.chambers (chamber_code, name)
VALUES
    ('house', 'House of Representatives'),
    ('senate', 'Senate'),
    ('joint', 'Joint Session')
ON CONFLICT (chamber_code) DO NOTHING;

CREATE TABLE IF NOT EXISTS congress.states (
    state_code           text PRIMARY KEY,
    name                 text NOT NULL,
    fips_code            text,
    is_territory         boolean NOT NULL DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.parties (
    party_code           text PRIMARY KEY,
    display_name         text NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.documents (
    document_hash        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url           text NOT NULL,
    content_type         text,
    content_length       bigint,
    sha1_hash            text,
    title                text,
    description          text,
    published_at         timestamptz,
    retrieved_at         timestamptz NOT NULL DEFAULT now(),
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.ingest_checkpoints (
    checkpoint_name      text PRIMARY KEY,
    resource_type        text NOT NULL,
    last_cursor          text,
    last_run_started_at  timestamptz,
    last_run_completed_at timestamptz,
    parameters           jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.members (
    bioguide_id          text PRIMARY KEY,
    first_name           text NOT NULL,
    middle_name          text,
    last_name            text NOT NULL,
    suffix               text,
    official_full_name   text,
    birthday             date,
    gender               text,
    biography            text,
    birthplace           text,
    death_date           date,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.member_terms (
    term_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bioguide_id          text NOT NULL REFERENCES congress.members (bioguide_id) ON DELETE CASCADE,
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number) ON DELETE CASCADE,
    chamber_code         text NOT NULL REFERENCES congress.chambers (chamber_code),
    state_code           text REFERENCES congress.states (state_code),
    district             text,
    party_code           text REFERENCES congress.parties (party_code),
    start_date           date NOT NULL,
    end_date             date,
    role_title           text,
    leadership_role      text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_member_terms_member ON congress.member_terms (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_member_terms_congress ON congress.member_terms (congress_number);

COMMIT;
