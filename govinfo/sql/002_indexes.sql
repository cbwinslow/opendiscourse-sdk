-- SPDX-License-Identifier: CC0-1.0
-- Secondary indexes, constraints, and views to optimize query workloads
-- for the govinfo schema.

BEGIN;

-- General indexes
CREATE INDEX IF NOT EXISTS idx_govinfo_packages_collection
    ON govinfo.packages(collection_code);
CREATE INDEX IF NOT EXISTS idx_govinfo_packages_last_modified
    ON govinfo.packages(last_modified);
CREATE INDEX IF NOT EXISTS idx_govinfo_packages_congress
    ON govinfo.packages(congress_number);
CREATE INDEX IF NOT EXISTS idx_govinfo_granules_package
    ON govinfo.granules(package_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_bulk_packages_status
    ON govinfo.bulk_packages(status);
CREATE INDEX IF NOT EXISTS idx_govinfo_bulk_packages_package
    ON govinfo.bulk_packages(package_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_download_log_identifier
    ON govinfo.download_log(identifier);

-- Bill-related indexes
CREATE INDEX IF NOT EXISTS idx_govinfo_bills_congress
    ON govinfo.bills(congress_number);
CREATE INDEX IF NOT EXISTS idx_govinfo_bills_bill_type_number
    ON govinfo.bills(bill_type, bill_number);
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_actions_bill_id
    ON govinfo.bill_actions(bill_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_actions_date
    ON govinfo.bill_actions(action_date);
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_summaries_bill_id
    ON govinfo.bill_summaries(bill_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_versions_bill_id
    ON govinfo.bill_versions(bill_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_committees_bill_id
    ON govinfo.bill_committees(bill_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_cosponsors_member
    ON govinfo.bill_cosponsors(member_id);

-- Voting indexes
CREATE INDEX IF NOT EXISTS idx_govinfo_votes_congress_chamber
    ON govinfo.votes(congress_number, chamber_code);
CREATE INDEX IF NOT EXISTS idx_govinfo_votes_bill
    ON govinfo.votes(bill_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_vote_actions_vote_id
    ON govinfo.vote_actions(vote_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_vote_totals_vote_id
    ON govinfo.vote_totals(vote_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_vote_ballots_vote_member
    ON govinfo.vote_ballots(vote_id, member_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_member_votes_member
    ON govinfo.member_votes(member_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_member_attendance_member
    ON govinfo.member_attendance(member_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_membership_votes_membership
    ON govinfo.membership_votes(membership_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_membership_attendance_membership
    ON govinfo.membership_attendance(membership_id);

-- Membership indexes
CREATE INDEX IF NOT EXISTS idx_govinfo_memberships_member
    ON govinfo.memberships(member_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_memberships_committee
    ON govinfo.memberships(committee_code);
CREATE INDEX IF NOT EXISTS idx_govinfo_member_terms_member
    ON govinfo.member_terms(member_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_member_roles_member
    ON govinfo.member_roles(member_id);

-- Materialized view to flatten bill summary metadata for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS govinfo.bill_summary_latest AS
SELECT DISTINCT ON (b.bill_id)
       b.bill_id,
       b.bill_type,
       b.bill_number,
       b.congress_number,
       bs.summary_date,
       bs.summary_text,
       bs.source,
       bs.is_official
FROM govinfo.bills b
JOIN govinfo.bill_summaries bs ON bs.bill_id = b.bill_id
ORDER BY b.bill_id, bs.summary_date DESC;

CREATE INDEX IF NOT EXISTS idx_govinfo_bill_summary_latest_bill
    ON govinfo.bill_summary_latest(bill_id);

COMMIT;
