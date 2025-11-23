-- Congress Members Data Verification Functions
-- These functions provide reusable utility functions for data analysis

-- Function: Get member count by congress
CREATE OR REPLACE FUNCTION congress.get_member_count_by_congress(
    p_congress_number INTEGER
) RETURNS INTEGER
LANGUAGE sql
AS $$
SELECT COUNT(*) 
FROM congress.member_terms 
WHERE congress_number = p_congress_number;
$$;

-- Function: Get unique member count
CREATE OR REPLACE FUNCTION congress.get_unique_member_count() 
RETURNS INTEGER
LANGUAGE sql
AS $$
SELECT COUNT(DISTINCT bioguide_id) 
FROM congress.members;
$$;

-- Function: Get total member terms count
CREATE OR REPLACE FUNCTION congress.get_total_member_terms_count() 
RETURNS INTEGER
LANGUAGE sql
AS $$
SELECT COUNT(*) 
FROM congress.member_terms;
$$;

-- Function: Get longest serving members
CREATE OR REPLACE FUNCTION congress.get_longest_serving_members(
    p_limit INTEGER DEFAULT 10
) RETURNS TABLE (
    bioguide_id TEXT,
    first_name TEXT,
    last_name TEXT,
    terms_served INTEGER,
    first_congress INTEGER,
    last_congress INTEGER
)
LANGUAGE sql
AS $$
SELECT 
    m.bioguide_id,
    m.first_name,
    m.last_name,
    COUNT(mt.congress_number) as terms_served,
    MIN(mt.congress_number) as first_congress,
    MAX(mt.congress_number) as last_congress
FROM congress.members m 
LEFT JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id 
GROUP BY m.bioguide_id, m.first_name, m.last_name 
ORDER BY terms_served DESC, m.last_name, m.first_name
LIMIT p_limit;
$$;

-- Function: Get party distribution for congress
CREATE OR REPLACE FUNCTION congress.get_party_distribution(
    p_congress_number INTEGER
) RETURNS TABLE (
    party_code TEXT,
    party_name TEXT,
    member_count INTEGER,
    percentage NUMERIC
)
LANGUAGE sql
AS $$
SELECT 
    mt.party_code,
    p.display_name as party_name,
    COUNT(*) as member_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM congress.member_terms mt
JOIN congress.parties p ON mt.party_code = p.party_code
WHERE mt.congress_number = p_congress_number
GROUP BY mt.party_code, p.display_name
ORDER BY member_count DESC;
$$;

-- Function: Get chamber distribution for congress
CREATE OR REPLACE FUNCTION congress.get_chamber_distribution(
    p_congress_number INTEGER
) RETURNS TABLE (
    chamber_code TEXT,
    chamber_name TEXT,
    member_count INTEGER
)
LANGUAGE sql
AS $$
SELECT 
    mt.chamber_code,
    c.name as chamber_name,
    COUNT(*) as member_count
FROM congress.member_terms mt
JOIN congress.chambers c ON mt.chamber_code = c.chamber_code
WHERE mt.congress_number = p_congress_number
GROUP BY mt.chamber_code, c.name
ORDER BY member_count DESC;
$$;

-- Function: Get state representation for congress
CREATE OR REPLACE FUNCTION congress.get_state_representation(
    p_congress_number INTEGER,
    p_chamber_code TEXT DEFAULT NULL
) RETURNS TABLE (
    state_code TEXT,
    state_name TEXT,
    member_count INTEGER
)
LANGUAGE sql
AS $$
SELECT 
    s.state_code,
    s.name as state_name,
    COUNT(*) as member_count
FROM congress.member_terms mt
JOIN congress.states s ON mt.state_code = s.state_code
WHERE mt.congress_number = p_congress_number
  AND (p_chamber_code IS NULL OR mt.chamber_code = p_chamber_code)
GROUP BY s.state_code, s.name
ORDER BY member_count DESC, s.name;
$$;

-- Function: Check member data completeness
CREATE OR REPLACE FUNCTION congress.check_member_data_completeness() 
RETURNS TABLE (
    check_type TEXT,
    issue_count INTEGER,
    percentage_issue NUMERIC
)
LANGUAGE sql
AS $$
SELECT 
    'Missing birthdays' as check_type,
    COUNT(*) as issue_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM congress.members), 2) as percentage_issue
FROM congress.members WHERE birthday IS NULL

UNION ALL

SELECT 
    'Missing genders' as check_type,
    COUNT(*) as issue_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM congress.members), 2) as percentage_issue
FROM congress.members WHERE gender IS NULL

UNION ALL

SELECT 
    'Missing biographies' as check_type,
    COUNT(*) as issue_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM congress.members), 2) as percentage_issue
FROM congress.members WHERE biography = ''

UNION ALL

SELECT 
    'Duplicate terms' as check_type,
    COUNT(*) as issue_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM congress.member_terms), 2) as percentage_issue
FROM (
    SELECT bioguide_id, congress_number, COUNT(*) as cnt
    FROM congress.member_terms 
    GROUP BY bioguide_id, congress_number 
    HAVING COUNT(*) > 1
) dup;
$$;

-- Function: Get member career path
CREATE OR REPLACE FUNCTION congress.get_member_career_path(
    p_bioguide_id TEXT
) RETURNS TABLE (
    congress_number INTEGER,
    chamber_code TEXT,
    chamber_name TEXT,
    state_code TEXT,
    state_name TEXT,
    party_code TEXT,
    party_name TEXT,
    district TEXT,
    start_date DATE,
    end_date DATE
)
LANGUAGE sql
AS $$
SELECT 
    mt.congress_number,
    mt.chamber_code,
    c.name as chamber_name,
    mt.state_code,
    s.name as state_name,
    mt.party_code,
    p.display_name as party_name,
    mt.district,
    mt.start_date,
    mt.end_date
FROM congress.member_terms mt
JOIN congress.chambers c ON mt.chamber_code = c.chamber_code
JOIN congress.states s ON mt.state_code = s.state_code
JOIN congress.parties p ON mt.party_code = p.party_code
WHERE mt.bioguide_id = p_bioguide_id
ORDER BY mt.congress_number;
$$;

-- Function: Get congress summary statistics
CREATE OR REPLACE FUNCTION congress.get_congress_summary(
    p_congress_number INTEGER
) RETURNS TABLE (
    metric_name TEXT,
    metric_value TEXT
)
LANGUAGE sql
AS $$
SELECT 'Total Members' as metric_name, COUNT(*)::TEXT as metric_value
FROM congress.member_terms WHERE congress_number = p_congress_number

UNION ALL

SELECT 'House Members', COUNT(*)::TEXT
FROM congress.member_terms 
WHERE congress_number = p_congress_number AND chamber_code = 'house'

UNION ALL

SELECT 'Senate Members', COUNT(*)::TEXT
FROM congress.member_terms 
WHERE congress_number = p_congress_number AND chamber_code = 'senate'

UNION ALL

SELECT 'States Represented', COUNT(DISTINCT state_code)::TEXT
FROM congress.member_terms 
WHERE congress_number = p_congress_number

UNION ALL

SELECT 'Parties Represented', COUNT(DISTINCT party_code)::TEXT
FROM congress.member_terms 
WHERE congress_number = p_congress_number;
$$;