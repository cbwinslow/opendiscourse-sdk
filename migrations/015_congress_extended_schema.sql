-- Extended Congress Schema
-- Adds support for Committee Reports, Prints, Hearings, and other missing data types

BEGIN;

-- Committee Reports
CREATE TABLE IF NOT EXISTS congress.committee_reports (
    report_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number),
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    committee_id         text REFERENCES congress.committees (committee_id),
    report_type          text, -- 'House Report', 'Senate Report', 'Executive Report'
    report_number        integer,
    title                text,
    citation             text,
    date                 date,
    text                 text,
    pdf_url              text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, report_type, report_number)
);

-- Committee Prints
CREATE TABLE IF NOT EXISTS congress.committee_prints (
    print_id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number),
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    committee_id         text REFERENCES congress.committees (committee_id),
    print_number         text, -- Can be alphanumeric
    title                text,
    date                 date,
    text                 text,
    pdf_url              text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, chamber_code, print_number)
);

-- Hearings
CREATE TABLE IF NOT EXISTS congress.hearings (
    hearing_id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number),
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    committee_id         text REFERENCES congress.committees (committee_id),
    hearing_number       text,
    title                text,
    date                 date,
    text                 text,
    pdf_url              text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, chamber_code, hearing_number)
);

-- Congressional Record (Daily)
CREATE TABLE IF NOT EXISTS congress.congressional_record (
    record_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number),
    session_number       integer,
    volume               integer,
    issue                integer,
    date                 date NOT NULL,
    full_text            text,
    pdf_url              text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (volume, issue)
);

-- Nominations
CREATE TABLE IF NOT EXISTS congress.nominations (
    nomination_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number),
    nomination_number    integer NOT NULL,
    received_date        date,
    description          text,
    committee_id         text REFERENCES congress.committees (committee_id),
    latest_action_date   date,
    latest_action_text   text,
    status               text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, nomination_number)
);

-- Treaties
CREATE TABLE IF NOT EXISTS congress.treaties (
    treaty_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number),
    treaty_number        integer NOT NULL,
    received_date        date,
    topic                text,
    committee_id         text REFERENCES congress.committees (committee_id),
    latest_action_date   date,
    latest_action_text   text,
    status               text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, treaty_number)
);

-- House Communications
CREATE TABLE IF NOT EXISTS congress.house_communications (
    communication_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number),
    communication_number integer NOT NULL,
    received_date        date,
    description          text,
    committee_id         text REFERENCES congress.committees (committee_id),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, communication_number)
);

-- Senate Communications
CREATE TABLE IF NOT EXISTS congress.senate_communications (
    communication_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number),
    communication_number integer NOT NULL,
    received_date        date,
    description          text,
    committee_id         text REFERENCES congress.committees (committee_id),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, communication_number)
);

COMMIT;
