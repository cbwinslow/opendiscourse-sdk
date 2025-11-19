-- 0002_create_legislative_entities.sql
--
-- Creates normalized tables for bills, amendments, committees, and associated metadata.

BEGIN;

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

CREATE INDEX IF NOT EXISTS idx_committee_members_committee ON congress.committee_members (committee_id);

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

CREATE INDEX IF NOT EXISTS idx_bills_congress_type ON congress.bills (congress_number, bill_type);
CREATE INDEX IF NOT EXISTS idx_bills_search_document ON congress.bills USING GIN (search_document);

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

CREATE INDEX IF NOT EXISTS idx_bill_actions_bill ON congress.bill_actions (bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_actions_date ON congress.bill_actions (action_date);

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

COMMIT;
