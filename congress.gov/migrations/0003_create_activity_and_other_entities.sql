-- 0003_create_activity_and_other_entities.sql
--
-- Adds roll calls, nominations, treaties, Congressional Record artifacts, and committee materials.

BEGIN;

CREATE TABLE IF NOT EXISTS congress.roll_calls (
    roll_call_id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number) ON DELETE CASCADE,
    chamber_code         text NOT NULL REFERENCES congress.chambers (chamber_code),
    session_number       integer NOT NULL,
    roll_number          integer NOT NULL,
    vote_question        text,
    vote_type            text,
    vote_result          text,
    issue                text,
    related_bill_id      uuid REFERENCES congress.bills (bill_id) ON DELETE SET NULL,
    vote_date            date NOT NULL,
    vote_time            time,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, chamber_code, session_number, roll_number)
);

CREATE TABLE IF NOT EXISTS congress.roll_call_votes (
    roll_call_id         uuid NOT NULL REFERENCES congress.roll_calls (roll_call_id) ON DELETE CASCADE,
    bioguide_id          text REFERENCES congress.members (bioguide_id) ON DELETE SET NULL,
    vote_position        text NOT NULL,
    vote_cast_at         timestamptz,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (roll_call_id, bioguide_id)
);

CREATE TABLE IF NOT EXISTS congress.nominations (
    nomination_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number) ON DELETE CASCADE,
    nomination_number    text NOT NULL,
    agency               text,
    position_title       text,
    received_date        date,
    description          text,
    status               text,
    last_action_date     date,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, nomination_number)
);

CREATE TABLE IF NOT EXISTS congress.nomination_actions (
    nomination_action_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nomination_id        uuid NOT NULL REFERENCES congress.nominations (nomination_id) ON DELETE CASCADE,
    action_date          date NOT NULL,
    action_text          text NOT NULL,
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    action_code          text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.nomination_candidates (
    nomination_id        uuid NOT NULL REFERENCES congress.nominations (nomination_id) ON DELETE CASCADE,
    candidate_name       text NOT NULL,
    candidate_bioguide_id text,
    residence            text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (nomination_id, candidate_name)
);

CREATE TABLE IF NOT EXISTS congress.treaties (
    treaty_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer REFERENCES congress.sessions (congress_number),
    treaty_number        text NOT NULL,
    title                text NOT NULL,
    subject              text,
    status               text,
    received_date        date,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (treaty_number)
);

CREATE TABLE IF NOT EXISTS congress.treaty_actions (
    treaty_action_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    treaty_id            uuid NOT NULL REFERENCES congress.treaties (treaty_id) ON DELETE CASCADE,
    action_date          date NOT NULL,
    action_text          text NOT NULL,
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.treaty_topics (
    treaty_id            uuid NOT NULL REFERENCES congress.treaties (treaty_id) ON DELETE CASCADE,
    topic                text NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (treaty_id, topic)
);

CREATE TABLE IF NOT EXISTS congress.congressional_record_sections (
    section_id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer REFERENCES congress.sessions (congress_number),
    issue_date           date NOT NULL,
    volume_number        integer,
    issue_number         integer,
    section_title        text,
    pdf_url              text,
    xml_url              text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.congressional_record_pages (
    page_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id           uuid NOT NULL REFERENCES congress.congressional_record_sections (section_id) ON DELETE CASCADE,
    page_number          integer NOT NULL,
    text_content         text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (section_id, page_number)
);

CREATE TABLE IF NOT EXISTS congress.floor_calendars (
    calendar_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer REFERENCES congress.sessions (congress_number),
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    calendar_name        text,
    calendar_date        date,
    description          text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.floor_calendar_entries (
    calendar_entry_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_id          uuid NOT NULL REFERENCES congress.floor_calendars (calendar_id) ON DELETE CASCADE,
    sequence_number      integer,
    bill_id              uuid REFERENCES congress.bills (bill_id),
    description          text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.committee_reports (
    report_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer REFERENCES congress.sessions (congress_number),
    report_number        text NOT NULL,
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    committee_id         text REFERENCES congress.committees (committee_id),
    title                text,
    url                  text,
    document_hash        uuid REFERENCES congress.documents (document_hash),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, report_number)
);

CREATE TABLE IF NOT EXISTS congress.hearings (
    hearing_id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer REFERENCES congress.sessions (congress_number),
    committee_id         text REFERENCES congress.committees (committee_id),
    hearing_title        text,
    hearing_date         date,
    location             text,
    video_url            text,
    text_url             text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS congress.hearing_witnesses (
    hearing_id           uuid NOT NULL REFERENCES congress.hearings (hearing_id) ON DELETE CASCADE,
    witness_name         text NOT NULL,
    witness_organization text,
    testimony_url        text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (hearing_id, witness_name)
);

COMMIT;
