-- Congress Members Data Verification Views
-- These views provide easy access to common verification queries

-- View: Member counts by congress
CREATE OR REPLACE VIEW congress.member_counts_by_congress AS
SELECT 
    congress_number, 
    COUNT(*) as members_count,
    COUNT(DISTINCT bioguide_id) as unique_members
FROM congress.member_terms 
GROUP BY congress_number 
ORDER BY congress_number;

-- View: Longest serving members
CREATE OR REPLACE VIEW congress.longest_serving_members AS
SELECT 
    m.bioguide_id,
    m.first_name,
    m.last_name,
    m.official_full_name,
    COUNT(mt.congress_number) as terms_served,
    MIN(mt.congress_number) as first_congress,
    MAX(mt.congress_number) as last_congress
FROM congress.members m 
LEFT JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id 
GROUP BY m.bioguide_id, m.first_name, m.last_name, m.official_full_name 
ORDER BY terms_served DESC, m.last_name, m.first_name;

-- View: Member detail with terms
CREATE OR REPLACE VIEW congress.member_term_details AS
SELECT 
    m.bioguide_id,
    m.first_name,
    m.last_name,
    m.official_full_name,
    mt.congress_number,
    mt.chamber_code,
    mt.state_code,
    mt.party_code,
    mt.start_date,
    mt.end_date,
    mt.district,
    mt.role_title,
    mt.leadership_role
FROM congress.members m 
JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id 
ORDER BY m.bioguide_id, mt.congress_number;

-- View: Party distribution by congress
CREATE OR REPLACE VIEW congress.party_distribution_by_congress AS
SELECT 
    mt.congress_number,
    p.display_name as party_name,
    COUNT(*) as member_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY mt.congress_number), 2) as percentage
FROM congress.member_terms mt
JOIN congress.parties p ON mt.party_code = p.party_code
GROUP BY mt.congress_number, p.party_code, p.display_name
ORDER BY mt.congress_number, member_count DESC;

-- View: State representation by congress
CREATE OR REPLACE VIEW congress.state_representation_by_congress AS
SELECT 
    mt.congress_number,
    s.name as state_name,
    mt.chamber_code,
    COUNT(*) as member_count
FROM congress.member_terms mt
JOIN congress.states s ON mt.state_code = s.state_code
GROUP BY mt.congress_number, s.name, mt.chamber_code
ORDER BY mt.congress_number, s.name, mt.chamber_code;

-- View: Chamber distribution by congress
CREATE OR REPLACE VIEW congress.chamber_distribution_by_congress AS
SELECT 
    mt.congress_number,
    c.name as chamber_name,
    COUNT(*) as member_count
FROM congress.member_terms mt
JOIN congress.chambers c ON mt.chamber_code = c.chamber_code
GROUP BY mt.congress_number, c.name
ORDER BY mt.congress_number, c.name;

-- View: Members with incomplete data
CREATE OR REPLACE VIEW congress.members_with_incomplete_data AS
SELECT 
    m.bioguide_id,
    m.first_name,
    m.last_name,
    CASE 
        WHEN m.birthday IS NULL THEN 'Missing birthday'
        WHEN m.gender IS NULL THEN 'Missing gender'
        WHEN m.biography = '' THEN 'Missing biography'
        ELSE 'Other missing data'
    END as missing_field
FROM congress.members m
WHERE m.birthday IS NULL 
   OR m.gender IS NULL 
   OR m.biography = ''
ORDER BY m.last_name, m.first_name;

-- View: Duplicate member terms (for data quality)
CREATE OR REPLACE VIEW congress.duplicate_member_terms AS
SELECT 
    bioguide_id,
    congress_number,
    COUNT(*) as duplicate_count
FROM congress.member_terms 
GROUP BY bioguide_id, congress_number 
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, bioguide_id;