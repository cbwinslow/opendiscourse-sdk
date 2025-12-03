-- Consolidated Congress.gov Schema
-- Combines the best features from migration and MCP versions
-- Uses normalized relational design with proper foreign keys
-- Includes comprehensive indexing and search capabilities

BEGIN;

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS congress;

-- Enable pgcrypto for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Core lookup tables
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

-- Document storage for full-text search
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

-- Ingestion tracking
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

-- Members and their terms
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

-- Committees
CREATE TABLE IF NOT EXISTS congress.committees (
    committee_id         text PRIMARY KEY,
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    name                 text NOT NULL,
    type                 text,
    url                  text,
    established_at       date,
    terminated_at        date,
    parent_committee_id  text REFERENCES congress.committees (committee_id) ON DELETE SET NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.committee_members (
    committee_member_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    committee_id         text NOT NULL REFERENCES congress.committees (committee_id) ON DELETE CASCADE,
    bioguide_id          text REFERENCES congress.members (bioguide_id) ON DELETE SET NULL,
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    congress_number      integer REFERENCES congress.sessions (congress_number),
    rank_in_committee    integer,
    title                text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Bills and related entities
CREATE TABLE IF NOT EXISTS congress.bills (
    bill_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number) ON DELETE CASCADE,
    bill_type            text NOT NULL,
    bill_number          integer NOT NULL,
    origin_chamber       text REFERENCES congress.chambers (chamber_code),
    introduced_date      date,
    latest_action_date   date,
    latest_action_text   text,
    policy_area          text,
    summary_text         text,
    summary_last_updated timestamptz,
    status               text,
    official_title       text,
    sponsor_bioguide_id  text REFERENCES congress.members (bioguide_id),
    committee_ids        text[] DEFAULT '{}',
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(official_title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(summary_text, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, bill_type, bill_number)
);

CREATE TABLE IF NOT EXISTS congress.bill_titles (
    bill_title_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    title_type           text NOT NULL,
    title                text NOT NULL,
    is_for_portion       boolean NOT NULL DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.bill_actions (
    bill_action_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    action_date          date NOT NULL,
    action_time          time,
    action_text          text NOT NULL,
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    action_code          text,
    source_system        text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.bill_subjects (
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    subject_term         text NOT NULL,
    is_major             boolean NOT NULL DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (bill_id, subject_term)
);

CREATE TABLE IF NOT EXISTS congress.bill_cosponsors (
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    bioguide_id          text NOT NULL REFERENCES congress.members (bioguide_id) ON DELETE CASCADE,
    cosponsored_date     date,
    is_original_cosponsor boolean DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (bill_id, bioguide_id)
);

CREATE TABLE IF NOT EXISTS congress.related_bills (
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    related_bill_type    text NOT NULL,
    related_bill_number  integer NOT NULL,
    related_congress     integer NOT NULL,
    relationship_type    text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (bill_id, related_bill_type, related_bill_number, related_congress)
);

CREATE TABLE IF NOT EXISTS congress.bill_text_versions (
    bill_text_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    version_code         text NOT NULL,
    version_name         text,
    version_date         date,
    gpo_pdf_url          text,
    xml_url              text,
    html_url             text,
    document_hash        uuid REFERENCES congress.documents (document_hash),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.bill_summaries (
    bill_summary_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    summary_date         date NOT NULL,
    summary_text         text NOT NULL,
    version_code         text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Amendments
CREATE TABLE IF NOT EXISTS congress.amendments (
    amendment_id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    amendment_number     text NOT NULL,
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number) ON DELETE CASCADE,
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    description          text,
    purpose              text,
    status               text,
    introduced_date      date,
    sponsor_bioguide_id  text REFERENCES congress.members (bioguide_id),
    bill_id              uuid REFERENCES congress.bills (bill_id) ON DELETE SET NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (amendment_number, congress_number)
);

CREATE TABLE IF NOT EXISTS congress.amendment_actions (
    amendment_action_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    amendment_id         uuid NOT NULL REFERENCES congress.amendments (amendment_id) ON DELETE CASCADE,
    action_date          date NOT NULL,
    action_text          text NOT NULL,
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    action_code          text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.amendment_sponsors (
    amendment_id         uuid NOT NULL REFERENCES congress.amendments (amendment_id) ON DELETE CASCADE,
    bioguide_id          text NOT NULL REFERENCES congress.members (bioguide_id) ON DELETE CASCADE,
    sponsor_type         text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (amendment_id, bioguide_id, sponsor_type)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_member_terms_member ON congress.member_terms (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_member_terms_congress ON congress.member_terms (congress_number);
CREATE INDEX IF NOT EXISTS idx_committee_members_committee ON congress.committee_members (committee_id);
CREATE INDEX IF NOT EXISTS idx_bills_congress_type ON congress.bills (congress_number, bill_type);
CREATE INDEX IF NOT EXISTS idx_bills_search_document ON congress.bills USING GIN (search_document);
CREATE INDEX IF NOT EXISTS idx_bill_actions_bill ON congress.bill_actions (bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_actions_date ON congress.bill_actions (action_date);
CREATE INDEX IF NOT EXISTS idx_documents_search ON congress.documents USING GIN (search_document);

COMMIT;