-- Optimized OpenStates Schema
-- Maps to existing normalized patterns while maintaining OCD compliance
-- Uses proven indexing strategies from other schemas

BEGIN;

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS openstates;

-- Core reference tables (optimized for state-level data)
CREATE TABLE IF NOT EXISTS openstates.jurisdictions (
    jurisdiction_id       text PRIMARY KEY, -- ocd-jurisdiction format
    name                 text NOT NULL,
    classification       text NOT NULL, -- state, municipality
    state_code           text NOT NULL, -- Two-letter state code
    url                  text,
    latest_bill_update   timestamptz,
    latest_people_update  timestamptz,
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS openstates.legislative_sessions (
    session_id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id       text NOT NULL REFERENCES openstates.jurisdictions(jurisdiction_id),
    identifier            text NOT NULL,
    name                 text NOT NULL,
    classification       text NOT NULL,
    start_date           date,
    end_date             date,
    is_active            boolean DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (jurisdiction_id, identifier)
);

-- Organizations (committees, legislatures)
CREATE TABLE IF NOT EXISTS openstates.organizations (
    organization_id       text PRIMARY KEY, -- ocd-organization format
    name                 text NOT NULL,
    classification       text NOT NULL, -- legislature, executive, committee
    jurisdiction_id       text REFERENCES openstates.jurisdictions(jurisdiction_id),
    parent_id            text REFERENCES openstates.organizations(organization_id),
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- People/legislators (optimized for search)
CREATE TABLE IF NOT EXISTS openstates.people (
    person_id            text PRIMARY KEY, -- ocd-person format
    name                 text NOT NULL,
    family_name          text NOT NULL,
    given_name           text NOT NULL,
    image                text,
    gender               text,
    biography            text,
    birth_date           date,
    death_date           date,
    primary_party        text,
    jurisdiction_id       text REFERENCES openstates.jurisdictions(jurisdiction_id),
    current_role_data     jsonb,
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(biography, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Bills (optimized for state-level search)
CREATE TABLE IF NOT EXISTS openstates.bills (
    bill_id              text PRIMARY KEY, -- ocd-bill format
    identifier           text NOT NULL,
    title                text NOT NULL,
    classification       text[] NOT NULL,
    subject              text[] NOT NULL,
    jurisdiction_id       text REFERENCES openstates.jurisdictions(jurisdiction_id),
    session_id           uuid REFERENCES openstates.legislative_sessions(session_id),
    from_organization_id text REFERENCES openstates.organizations(organization_id),
    first_action_date    date,
    latest_action_date   date,
    latest_action_desc   text,
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(latest_action_desc, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Bill actions (optimized for timeline queries)
CREATE TABLE IF NOT EXISTS openstates.bill_actions (
    action_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              text NOT NULL REFERENCES openstates.bills(bill_id) ON DELETE CASCADE,
    description          text NOT NULL,
    date                 date NOT NULL,
    classification       text[] NOT NULL,
    order_sequence       integer NOT NULL,
    organization_id      text REFERENCES openstates.organizations(organization_id),
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(description, '')), 'A')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Bill sponsorships (optimized for sponsor analysis)
CREATE TABLE IF NOT EXISTS openstates.bill_sponsorships (
    sponsorship_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              text NOT NULL REFERENCES openstates.bills(bill_id) ON DELETE CASCADE,
    person_id            text REFERENCES openstates.people(person_id),
    organization_id      text REFERENCES openstates.organizations(organization_id),
    name                 text NOT NULL,
    is_primary           boolean NOT NULL DEFAULT false,
    classification       text NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Vote events (optimized for vote analysis)
CREATE TABLE IF NOT EXISTS openstates.vote_events (
    vote_id              text PRIMARY KEY, -- ocd-vote format
    identifier           text NOT NULL,
    motion_text          text NOT NULL,
    motion_classification text[] NOT NULL,
    start_date           timestamptz NOT NULL,
    result               text NOT NULL,
    bill_id              text REFERENCES openstates.bills(bill_id),
    organization_id      text NOT NULL REFERENCES openstates.organizations(organization_id),
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(motion_text, '')), 'A')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Person votes (optimized for voting patterns)
CREATE TABLE IF NOT EXISTS openstates.person_votes (
    vote_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vote_event_id        text NOT NULL REFERENCES openstates.vote_events(vote_id) ON DELETE CASCADE,
    person_id            text REFERENCES openstates.people(person_id),
    option               text NOT NULL,
    voter_name           text NOT NULL,
    note                 text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (vote_event_id, person_id)
);

-- Memberships (optimized for committee analysis)
CREATE TABLE IF NOT EXISTS openstates.memberships (
    membership_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id            text REFERENCES openstates.people(person_id),
    organization_id      text REFERENCES openstates.organizations(organization_id),
    label                text NOT NULL,
    role                 text NOT NULL,
    start_date           date,
    end_date             date,
    post_id              text,
    on_behalf_of_id      text REFERENCES openstates.organizations(organization_id),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Posts (legislative positions)
CREATE TABLE IF NOT EXISTS openstates.posts (
    post_id              text PRIMARY KEY, -- ocd-post format
    label                text NOT NULL,
    role                 text NOT NULL,
    jurisdiction_id       text REFERENCES openstates.jurisdictions(jurisdiction_id),
    organization_id      text REFERENCES openstates.organizations(organization_id),
    start_date           date,
    end_date             date,
    maximum_memberships  integer DEFAULT 1,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Events (committees, hearings)
CREATE TABLE IF NOT EXISTS openstates.events (
    event_id             text PRIMARY KEY, -- ocd-event format
    name                 text NOT NULL,
    description          text NOT NULL,
    classification       text NOT NULL,
    start_date           timestamptz,
    end_date             timestamptz,
    all_day              boolean DEFAULT false,
    timezone             text,
    status               text NOT NULL,
    jurisdiction_id       text NOT NULL REFERENCES openstates.jurisdictions(jurisdiction_id),
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_openstates_jurisdictions_state ON openstates.jurisdictions(state_code);
CREATE INDEX IF NOT EXISTS idx_openstates_jurisdictions_search ON openstates.jurisdictions USING GIN (search_document);

CREATE INDEX IF NOT EXISTS idx_openstates_people_jurisdiction ON openstates.people(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_openstates_people_party ON openstates.people(primary_party);
CREATE INDEX IF NOT EXISTS idx_openstates_people_search ON openstates.people USING GIN (search_document);

CREATE INDEX IF NOT EXISTS idx_openstates_bills_jurisdiction ON openstates.bills(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_openstates_bills_session ON openstates.bills(session_id);
CREATE INDEX IF NOT EXISTS idx_openstates_bills_dates ON openstates.bills(latest_action_date, first_action_date);
CREATE INDEX IF NOT EXISTS idx_openstates_bills_search ON openstates.bills USING GIN (search_document);
CREATE INDEX IF NOT EXISTS idx_openstates_bills_subjects ON openstates.bills USING GIN (classification);

CREATE INDEX IF NOT EXISTS idx_openstates_bill_actions_bill ON openstates.bill_actions(bill_id, order_sequence);
CREATE INDEX IF NOT EXISTS idx_openstates_bill_actions_date ON openstates.bill_actions(date);
CREATE INDEX IF NOT EXISTS idx_openstates_bill_actions_search ON openstates.bill_actions USING GIN (search_document);

CREATE INDEX IF NOT EXISTS idx_openstates_sponsorships_bill ON openstates.bill_sponsorships(bill_id);
CREATE INDEX IF NOT EXISTS idx_openstates_sponsorships_person ON openstates.bill_sponsorships(person_id);

CREATE INDEX IF NOT EXISTS idx_openstates_vote_events_bill ON openstates.vote_events(bill_id);
CREATE INDEX IF NOT EXISTS idx_openstates_vote_events_org ON openstates.vote_events(organization_id);
CREATE INDEX IF NOT EXISTS idx_openstates_vote_events_date ON openstates.vote_events(start_date);
CREATE INDEX IF NOT EXISTS idx_openstates_vote_events_search ON openstates.vote_events USING GIN (search_document);

CREATE INDEX IF NOT EXISTS idx_openstates_person_votes_vote ON openstates.person_votes(vote_event_id);
CREATE INDEX IF NOT EXISTS idx_openstates_person_votes_person ON openstates.person_votes(person_id);

CREATE INDEX IF NOT EXISTS idx_openstates_memberships_person ON openstates.memberships(person_id);
CREATE INDEX IF NOT EXISTS idx_openstates_memberships_org ON openstates.memberships(organization_id);
CREATE INDEX IF NOT EXISTS idx_openstates_memberships_dates ON openstates.memberships(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_openstates_events_jurisdiction ON openstates.events(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_openstates_events_dates ON openstates.events(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_openstates_events_search ON openstates.events USING GIN (search_document);

COMMIT;
