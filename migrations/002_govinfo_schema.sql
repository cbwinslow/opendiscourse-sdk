-- Consolidated GovInfo Schema
-- Combines the best features from migration and MCP versions
-- Uses comprehensive relational design with proper foreign keys
-- Includes full-text search and processing capabilities

BEGIN;

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS govinfo;

-- Core reference tables
CREATE TABLE IF NOT EXISTS govinfo.collections (
    collection_code          text PRIMARY KEY,
    collection_name          text NOT NULL,
    package_count            bigint,
    granule_count            bigint,
    description              text,
    source_url               text,
    last_indexed_at          timestamptz,
    created_at               timestamptz DEFAULT now(),
    updated_at               timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS govinfo.chambers (
    chamber_code             text PRIMARY KEY,
    chamber_name             text NOT NULL,
    chamber_type             text,
    description              text
);

CREATE TABLE IF NOT EXISTS govinfo.congresses (
    congress_number          integer PRIMARY KEY,
    start_date               date,
    end_date                 date,
    session_count            integer,
    description              text
);

CREATE TABLE IF NOT EXISTS govinfo.sessions (
    session_id               text PRIMARY KEY,
    congress_number          integer REFERENCES govinfo.congresses(congress_number),
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    session_number           integer NOT NULL,
    session_type             text,
    start_date               date,
    end_date                 date,
    description              text
);

CREATE TABLE IF NOT EXISTS govinfo.parties (
    party_code               text PRIMARY KEY,
    party_name               text NOT NULL,
    ideology_score           numeric,
    notes                    text
);

CREATE TABLE IF NOT EXISTS govinfo.committees (
    committee_code           text PRIMARY KEY,
    committee_name           text NOT NULL,
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    parent_committee_code    text REFERENCES govinfo.committees(committee_code),
    type                     text,
    established_date         date,
    terminated_date          date,
    url                      text,
    jurisdiction             text
);

-- Members and their roles
CREATE TABLE IF NOT EXISTS govinfo.members (
    member_id                text PRIMARY KEY,
    bioguide_id              text UNIQUE,
    first_name               text,
    middle_name              text,
    last_name                text,
    suffix                   text,
    full_name                text,
    preferred_name           text,
    birthday                 date,
    gender                   text,
    party_code               text REFERENCES govinfo.parties(party_code),
    state                    text,
    district                 text,
    url                      text,
    twitter_handle           text,
    youtube_handle           text,
    facebook_handle          text,
    biography_text           text,
    photo_url                text,
    created_at               timestamptz DEFAULT now(),
    updated_at               timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS govinfo.member_terms (
    member_term_id           bigserial PRIMARY KEY,
    member_id                text REFERENCES govinfo.members(member_id),
    congress_number          integer REFERENCES govinfo.congresses(congress_number),
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    start_date               date,
    end_date                 date,
    state                    text,
    district                 text,
    party_code               text REFERENCES govinfo.parties(party_code),
    status                   text,
    office_room              text,
    phone                    text,
    fax                      text,
    contact_url              text,
    created_at               timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS govinfo.memberships (
    membership_id            text PRIMARY KEY,
    member_id                text REFERENCES govinfo.members(member_id),
    committee_code           text REFERENCES govinfo.committees(committee_code),
    role                     text,
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    congress_number          integer REFERENCES govinfo.congresses(congress_number),
    start_date               date,
    end_date                 date,
    is_chair                 boolean,
    is_vice_chair            boolean,
    rank_order               integer,
    notes                    text
);

-- Package and granule management
CREATE TABLE IF NOT EXISTS govinfo.packages (
    package_id               text PRIMARY KEY,
    collection_code          text REFERENCES govinfo.collections(collection_code),
    title                    text,
    congress_number          integer REFERENCES govinfo.congresses(congress_number),
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    bill_type                text,
    bill_number              text,
    document_class           text,
    doc_number               text,
    granule_count            integer,
    date_issued              date,
    last_modified            timestamptz,
    summary                  text,
    origin                   text,
    urls                     jsonb,
    metadata                 jsonb,
    retrieved_at             timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS govinfo.granules (
    granule_id               text PRIMARY KEY,
    package_id               text REFERENCES govinfo.packages(package_id) ON DELETE CASCADE,
    granule_class            text,
    title                    text,
    sequence_number          integer,
    granule_date             date,
    last_modified            timestamptz,
    metadata                 jsonb,
    text_url                 text,
    pdf_url                  text,
    xml_url                  text,
    zip_url                  text
);

-- Bulk data management
CREATE TABLE IF NOT EXISTS govinfo.bulk_packages (
    bulk_package_id          bigserial PRIMARY KEY,
    collection_code          text REFERENCES govinfo.collections(collection_code),
    package_id               text REFERENCES govinfo.packages(package_id),
    download_url             text NOT NULL,
    checksum                 text,
    size_bytes               bigint,
    last_modified            timestamptz,
    local_path               text,
    status                   text,
    retrieved_at             timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS govinfo.bulk_files (
    bulk_file_id             bigserial PRIMARY KEY,
    bulk_package_id          bigint REFERENCES govinfo.bulk_packages(bulk_package_id) ON DELETE CASCADE,
    file_name                text NOT NULL,
    file_type                text,
    content_url              text,
    size_bytes               bigint,
    checksum                 text,
    extracted_path           text,
    metadata                 jsonb
);

-- Bills and related entities
CREATE TABLE IF NOT EXISTS govinfo.bills (
    bill_id                  text PRIMARY KEY,
    package_id               text UNIQUE REFERENCES govinfo.packages(package_id) ON DELETE CASCADE,
    bill_type                text,
    bill_number              text,
    congress_number          integer REFERENCES govinfo.congresses(congress_number),
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    origin_chamber           text,
    introduced_date          date,
    latest_action_date       date,
    latest_action_text       text,
    status                   text,
    subjects_primary         text,
    subjects_secondary       text[],
    committees               text[],
    sponsors                 jsonb,
    cosponsors               jsonb,
    summaries                jsonb,
    text_versions            jsonb,
    related_packages         jsonb,
    last_updated_at          timestamptz
);

CREATE TABLE IF NOT EXISTS govinfo.bill_versions (
    bill_version_id          bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    version_code             text,
    version_name             text,
    issued_date              date,
    urls                     jsonb,
    is_latest                boolean,
    metadata                 jsonb,
    UNIQUE (bill_id, version_code)
);

CREATE TABLE IF NOT EXISTS govinfo.bill_summaries (
    bill_summary_id          bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    summary_date             date,
    summary_text             text,
    source                   text,
    is_official              boolean,
    metadata                 jsonb,
    UNIQUE (bill_id, summary_date, source)
);

CREATE TABLE IF NOT EXISTS govinfo.bill_actions (
    bill_action_id           bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    action_date              date,
    action_time              time,
    action_text              text,
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    action_type              text,
    committees               text[],
    roll_call_number         text,
    recorded_vote_id         text,
    UNIQUE (bill_id, action_date, action_time, action_text)
);

CREATE TABLE IF NOT EXISTS govinfo.bill_related_entities (
    bill_related_id          bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    related_type             text,
    related_identifier       text,
    title                    text,
    relationship             text,
    metadata                 jsonb
);

CREATE TABLE IF NOT EXISTS govinfo.bill_subjects (
    bill_subject_id          bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    subject_term             text,
    subject_type             text,
    is_primary               boolean DEFAULT false,
    UNIQUE (bill_id, subject_term, subject_type)
);

CREATE TABLE IF NOT EXISTS govinfo.bill_committees (
    bill_committee_id        bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    committee_code           text REFERENCES govinfo.committees(committee_code),
    role                     text,
    referral_date            date,
    report_number            text,
    UNIQUE (bill_id, committee_code, referral_date)
);

CREATE TABLE IF NOT EXISTS govinfo.bill_cosponsors (
    bill_cosponsor_id        bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    member_id                text REFERENCES govinfo.members(member_id),
    cosponsor_type           text,
    cosponsored_date         date,
    withdrew_date            date,
    UNIQUE (bill_id, member_id)
);

CREATE TABLE IF NOT EXISTS govinfo.bill_amendments (
    bill_amendment_id        bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    amendment_number         text,
    amendment_type           text,
    sponsor_member_id        text REFERENCES govinfo.members(member_id),
    introduced_date          date,
    status_text              text,
    status_date              date,
    urls                     jsonb
);

CREATE TABLE IF NOT EXISTS govinfo.bill_law_references (
    bill_law_reference_id    bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    law_type                 text,
    citation                 text,
    public_law_number        text,
    statute_at_large_cite    text,
    usc_cite                 text,
    notes                    text
);

-- Votes and voting records
CREATE TABLE IF NOT EXISTS govinfo.votes (
    vote_id                  text PRIMARY KEY,
    package_id               text REFERENCES govinfo.packages(package_id),
    congress_number          integer REFERENCES govinfo.congresses(congress_number),
    session_id               text REFERENCES govinfo.sessions(session_id),
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    vote_number              integer,
    vote_question            text,
    vote_type                text,
    vote_result              text,
    vote_date                date,
    vote_time                time,
    vote_title               text,
    bill_id                  text REFERENCES govinfo.bills(bill_id),
    related_amendment        text,
    related_matter           text,
    metadata                 jsonb
);

CREATE TABLE IF NOT EXISTS govinfo.vote_actions (
    vote_action_id           bigserial PRIMARY KEY,
    vote_id                  text REFERENCES govinfo.votes(vote_id) ON DELETE CASCADE,
    action_sequence          integer,
    action_text              text,
    action_time              timestamptz,
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    recorded_vote_id         text,
    metadata                 jsonb,
    UNIQUE (vote_id, action_sequence)
);

CREATE TABLE IF NOT EXISTS govinfo.vote_totals (
    vote_total_id            bigserial PRIMARY KEY,
    vote_id                  text REFERENCES govinfo.votes(vote_id) ON DELETE CASCADE,
    total_yes                integer,
    total_no                 integer,
    total_present            integer,
    total_not_voting         integer,
    majority_requirement     text,
    result_text              text,
    metadata                 jsonb,
    UNIQUE (vote_id)
);

CREATE TABLE IF NOT EXISTS govinfo.vote_ballots (
    vote_ballot_id           bigserial PRIMARY KEY,
    vote_id                  text REFERENCES govinfo.votes(vote_id) ON DELETE CASCADE,
    member_id                text REFERENCES govinfo.members(member_id),
    vote_cast                text,
    vote_pair                text,
    vote_group               text,
    vote_note                text,
    is_vote_changed          boolean,
    changed_at               timestamptz,
    UNIQUE (vote_id, member_id)
);

CREATE TABLE IF NOT EXISTS govinfo.member_votes (
    member_vote_id           bigserial PRIMARY KEY,
    member_id                text REFERENCES govinfo.members(member_id),
    vote_id                  text REFERENCES govinfo.votes(vote_id) ON DELETE CASCADE,
    vote_cast                text,
    vote_pair                text,
    vote_note                text,
    was_present              boolean,
    voted_at                 timestamptz,
    source                   text,
    UNIQUE (member_id, vote_id)
);

-- Attendance and activity tracking
CREATE TABLE IF NOT EXISTS govinfo.member_attendance (
    member_attendance_id     bigserial PRIMARY KEY,
    member_id                text REFERENCES govinfo.members(member_id),
    session_id               text REFERENCES govinfo.sessions(session_id),
    congress_number          integer REFERENCES govinfo.congresses(congress_number),
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    attended_votes           integer,
    missed_votes             integer,
    present_votes            integer,
    leave_votes              integer,
    attendance_rate          numeric,
    report_date              date,
    source                   text,
    UNIQUE (member_id, session_id, congress_number, chamber_code)
);

CREATE TABLE IF NOT EXISTS govinfo.membership_votes (
    membership_vote_id       bigserial PRIMARY KEY,
    membership_id            text REFERENCES govinfo.memberships(membership_id) ON DELETE CASCADE,
    vote_id                  text REFERENCES govinfo.votes(vote_id) ON DELETE CASCADE,
    vote_cast                text,
    voted_at                 timestamptz,
    UNIQUE (membership_id, vote_id)
);

CREATE TABLE IF NOT EXISTS govinfo.membership_attendance (
    membership_attendance_id bigserial PRIMARY KEY,
    membership_id            text REFERENCES govinfo.memberships(membership_id) ON DELETE CASCADE,
    session_id               text REFERENCES govinfo.sessions(session_id),
    attended_votes           integer,
    missed_votes             integer,
    attendance_rate          numeric,
    report_date              date,
    UNIQUE (membership_id, session_id)
);

CREATE TABLE IF NOT EXISTS govinfo.membership_bills (
    membership_bill_id       bigserial PRIMARY KEY,
    membership_id            text REFERENCES govinfo.memberships(membership_id) ON DELETE CASCADE,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    activity_type            text,
    activity_date            date,
    notes                    text,
    UNIQUE (membership_id, bill_id)
);

CREATE TABLE IF NOT EXISTS govinfo.member_bill_positions (
    member_bill_position_id  bigserial PRIMARY KEY,
    member_id                text REFERENCES govinfo.members(member_id),
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    position_type            text,
    position_date            date,
    notes                    text,
    UNIQUE (member_id, bill_id)
);

CREATE TABLE IF NOT EXISTS govinfo.attendance_records (
    attendance_record_id     bigserial PRIMARY KEY,
    vote_id                  text REFERENCES govinfo.votes(vote_id) ON DELETE CASCADE,
    member_id                text REFERENCES govinfo.members(member_id),
    attendance_status        text,
    reason                   text,
    reported_at              timestamptz,
    UNIQUE (vote_id, member_id)
);

CREATE TABLE IF NOT EXISTS govinfo.member_roles (
    member_role_id           bigserial PRIMARY KEY,
    member_id                text REFERENCES govinfo.members(member_id),
    role_type                text,
    role_description         text,
    start_date               date,
    end_date                 date,
    chamber_code             text REFERENCES govinfo.chambers(chamber_code),
    congress_number          integer REFERENCES govinfo.congresses(congress_number),
    UNIQUE (member_id, role_type, start_date)
);

-- System and tracking tables
CREATE TABLE IF NOT EXISTS govinfo.collections_audit (
    audit_id                 bigserial PRIMARY KEY,
    collection_code          text REFERENCES govinfo.collections(collection_code),
    last_modified_start      timestamptz,
    last_modified_end        timestamptz,
    offset_mark              text,
    page_size                integer,
    request_url              text,
    response_metadata        jsonb,
    captured_at              timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS govinfo.download_log (
    download_id              bigserial PRIMARY KEY,
    source_type              text NOT NULL,
    identifier               text,
    url                      text NOT NULL,
    http_status              integer,
    duration_ms              integer,
    bytes_transferred        bigint,
    error_message            text,
    attempted_at             timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS govinfo.api_snapshots (
    snapshot_id              bigserial PRIMARY KEY,
    source_endpoint          text NOT NULL,
    request_parameters       jsonb NOT NULL,
    response_payload         jsonb,
    captured_at              timestamptz DEFAULT now(),
    expires_at               timestamptz,
    checksum                 text
);

CREATE TABLE IF NOT EXISTS govinfo.errors (
    error_id                 bigserial PRIMARY KEY,
    context                  text,
    identifier               text,
    error_payload            jsonb,
    retryable                boolean DEFAULT true,
    created_at               timestamptz DEFAULT now(),
    resolved_at              timestamptz
);

COMMIT;