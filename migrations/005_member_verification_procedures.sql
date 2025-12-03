-- Congress Members Data Verification Procedures
-- These procedures provide common data quality and verification operations

-- Procedure: Get comprehensive member statistics
CREATE OR REPLACE PROCEDURE congress.get_member_statistics(
    IN p_congress_number INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_total_members INTEGER;
    v_unique_members INTEGER;
    v_total_terms INTEGER;
    v_congress_count INTEGER;
BEGIN
    -- Get overall statistics
    SELECT COUNT(DISTINCT bioguide_id) INTO v_unique_members
    FROM congress.members;
    
    SELECT COUNT(*) INTO v_total_terms
    FROM congress.member_terms;
    
    IF p_congress_number IS NOT NULL THEN
        -- Get statistics for specific congress
        SELECT COUNT(*) INTO v_total_members
        FROM congress.member_terms 
        WHERE congress_number = p_congress_number;
        
        RAISE NOTICE 'Congress % Statistics:', p_congress_number;
        RAISE NOTICE '  Members: %', v_total_members;
        RAISE NOTICE '  Total Unique Members (All Time): %', v_unique_members;
        RAISE NOTICE '  Total Terms (All Time): %', v_total_terms;
    ELSE
        -- Get overall statistics
        SELECT COUNT(DISTINCT congress_number) INTO v_congress_count
        FROM congress.member_terms;
        
        RAISE NOTICE 'Overall Congress Statistics:';
        RAISE NOTICE '  Total Unique Members: %', v_unique_members;
        RAISE NOTICE '  Total Member Terms: %', v_total_terms;
        RAISE NOTICE '  Congresses Covered: %', v_congress_count;
    END IF;
END;
$$;

-- Procedure: Check data quality issues
CREATE OR REPLACE PROCEDURE congress.check_data_quality()
LANGUAGE plpgsql
AS $$
DECLARE
    v_missing_birthdays INTEGER;
    v_missing_genders INTEGER;
    v_missing_biographies INTEGER;
    v_duplicate_terms INTEGER;
    v_orphaned_terms INTEGER;
BEGIN
    -- Check for missing member data
    SELECT COUNT(*) INTO v_missing_birthdays
    FROM congress.members WHERE birthday IS NULL;
    
    SELECT COUNT(*) INTO v_missing_genders
    FROM congress.members WHERE gender IS NULL;
    
    SELECT COUNT(*) INTO v_missing_biographies
    FROM congress.members WHERE biography = '';
    
    -- Check for duplicate terms
    SELECT COUNT(*) INTO v_duplicate_terms
    FROM (
        SELECT bioguide_id, congress_number, COUNT(*) as cnt
        FROM congress.member_terms 
        GROUP BY bioguide_id, congress_number 
        HAVING COUNT(*) > 1
    ) dup;
    
    -- Check for orphaned terms (terms without matching members)
    SELECT COUNT(*) INTO v_orphaned_terms
    FROM congress.member_terms mt
    LEFT JOIN congress.members m ON mt.bioguide_id = m.bioguide_id
    WHERE m.bioguide_id IS NULL;
    
    RAISE NOTICE 'Data Quality Report:';
    RAISE NOTICE '  Members missing birthdays: %', v_missing_birthdays;
    RAISE NOTICE '  Members missing genders: %', v_missing_genders;
    RAISE NOTICE '  Members missing biographies: %', v_missing_biographies;
    RAISE NOTICE '  Duplicate member terms: %', v_duplicate_terms;
    RAISE NOTICE '  Orphaned terms: %', v_orphaned_terms;
    
    IF v_missing_birthdays = 0 AND v_missing_genders = 0 AND 
       v_missing_biographies = 0 AND v_duplicate_terms = 0 AND 
       v_orphaned_terms = 0 THEN
        RAISE NOTICE '✅ All data quality checks passed!';
    ELSE
        RAISE NOTICE '⚠️  Data quality issues found. See above for details.';
    END IF;
END;
$$;

-- Procedure: Clean duplicate member terms
CREATE OR REPLACE PROCEDURE congress.clean_duplicate_terms()
LANGUAGE plpgsql
AS $$
DECLARE
    v_duplicates_removed INTEGER;
BEGIN
    -- Remove duplicate member terms, keeping the first occurrence
    DELETE FROM congress.member_terms 
    WHERE ctid NOT IN (
        SELECT DISTINCT ON (bioguide_id, congress_number) ctid 
        FROM congress.member_terms 
        ORDER BY bioguide_id, congress_number, ctid
    );
    
    GET DIAGNOSTICS v_duplicates_removed = ROW_COUNT;
    
    RAISE NOTICE 'Cleaned % duplicate member terms', v_duplicates_removed;
END;
$$;

-- Procedure: Get member career summary
CREATE OR REPLACE PROCEDURE congress.get_member_career_summary(
    IN p_bioguide_id TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_member_name TEXT;
    v_terms_served INTEGER;
    v_first_congress INTEGER;
    v_last_congress INTEGER;
    v_chambers_served TEXT;
    v_parties_affiliated TEXT;
    v_states_represented TEXT;
BEGIN
    -- Get member info
    SELECT first_name || ' ' || last_name INTO v_member_name
    FROM congress.members 
    WHERE bioguide_id = p_bioguide_id;
    
    -- Get career statistics
    SELECT COUNT(*) INTO v_terms_served
    FROM congress.member_terms 
    WHERE bioguide_id = p_bioguide_id;
    
    SELECT MIN(congress_number), MAX(congress_number) INTO v_first_congress, v_last_congress
    FROM congress.member_terms 
    WHERE bioguide_id = p_bioguide_id;
    
    -- Get chambers served
    SELECT STRING_AGG(DISTINCT chamber_code, ', ') INTO v_chambers_served
    FROM congress.member_terms 
    WHERE bioguide_id = p_bioguide_id;
    
    -- Get parties affiliated
    SELECT STRING_AGG(DISTINCT party_code, ', ') INTO v_parties_affiliated
    FROM congress.member_terms 
    WHERE bioguide_id = p_bioguide_id;
    
    -- Get states represented
    SELECT STRING_AGG(DISTINCT state_code, ', ') INTO v_states_represented
    FROM congress.member_terms 
    WHERE bioguide_id = p_bioguide_id;
    
    RAISE NOTICE 'Career Summary for % (%)', v_member_name, p_bioguide_id;
    RAISE NOTICE '  Terms Served: %', v_terms_served;
    RAISE NOTICE '  Congress Range: % to %', v_first_congress, v_last_congress;
    RAISE NOTICE '  Chambers: %', v_chambers_served;
    RAISE NOTICE '  Parties: %', v_parties_affiliated;
    RAISE NOTICE '  States: %', v_states_represented;
END;
$$;