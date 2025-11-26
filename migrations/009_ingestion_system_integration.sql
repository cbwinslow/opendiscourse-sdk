-- =============================================
-- Complete Ingestion System Database Integration (Fixed Order)
-- =============================================

-- Create ingestion schema
CREATE SCHEMA IF NOT EXISTS ingestion;

-- =============================================
-- Custom Types for Ingestion (must be created first)
-- =============================================

-- Congress member type
CREATE TYPE ingestion.congress_member_type AS (
    bioguide_id TEXT,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    suffix TEXT,
    official_full_name TEXT,
    birthday TEXT,
    gender TEXT,
    biography TEXT,
    birthplace TEXT,
    death_date TEXT
);

-- GovInfo member type
CREATE TYPE ingestion.govinfo_member_type AS (
    member_id TEXT,
    bioguide_id TEXT,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    suffix TEXT,
    full_name TEXT,
    preferred_name TEXT,
    birthday TEXT,
    gender TEXT,
    party_code TEXT,
    state TEXT,
    district TEXT,
    url TEXT,
    twitter_handle TEXT,
    youtube_handle TEXT,
    facebook_handle TEXT,
    biography_text TEXT,
    photo_url TEXT
);

-- OpenStates person type
CREATE TYPE ingestion.openstates_person_type AS (
    person_id TEXT,
    name TEXT,
    family_name TEXT,
    given_name TEXT,
    image TEXT,
    gender TEXT,
    biography TEXT,
    birth_date TEXT,
    death_date TEXT,
    primary_party TEXT,
    jurisdiction_id TEXT,
    current_role_data JSONB
);

-- =============================================
-- Ingestion Functions and Procedures
-- =============================================

-- Function to start an ingestion job
CREATE OR REPLACE FUNCTION ingestion.start_ingestion_job(
    p_job_name VARCHAR(255),
    p_data_source VARCHAR(100),
    p_table_name VARCHAR(100),
    p_record_type VARCHAR(100),
    p_total_estimated INTEGER DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
)
RETURNS INTEGER AS $$
DECLARE
    v_job_id INTEGER;
BEGIN
    INSERT INTO ingestion.ingestion_jobs (
        job_name, data_source, table_name, record_type,
        total_estimated, metadata, status
    ) VALUES (
        p_job_name, p_data_source, p_table_name, p_record_type,
        p_total_estimated, p_metadata, 'running'
    ) RETURNING id INTO v_job_id;
    
    RETURN v_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update ingestion progress
CREATE OR REPLACE FUNCTION ingestion.update_ingestion_progress(
    p_job_id INTEGER,
    p_processed_records INTEGER DEFAULT NULL,
    p_failed_records INTEGER DEFAULT NULL,
    p_current_record_id VARCHAR(500) DEFAULT NULL,
    p_error_details JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE ingestion.ingestion_jobs SET
        processed_records = COALESCE(p_processed_records, processed_records),
        failed_records = COALESCE(p_failed_records, failed_records),
        current_record_id = p_current_record_id,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_job_id;
    
    -- Log error if provided
    IF p_error_details IS NOT NULL THEN
        INSERT INTO ingestion.ingestion_errors (
            job_id, error_type, error_message, record_id, error_metadata
        ) VALUES (
            p_job_id, 
            p_error_details->>'error_type',
            p_error_details->>'error_message',
            p_current_record_id,
            p_error_details
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to complete ingestion job
CREATE OR REPLACE FUNCTION ingestion.complete_ingestion_job(
    p_job_id INTEGER,
    p_final_status VARCHAR(20) DEFAULT 'completed',
    p_final_metadata JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE ingestion.ingestion_jobs SET
        status = p_final_status,
        completed_at = CURRENT_TIMESTAMP,
        metadata = metadata || COALESCE(p_final_metadata, '{}'),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get ingestion job status
CREATE OR REPLACE FUNCTION ingestion.get_job_status(p_job_id INTEGER)
RETURNS TABLE (
    id INTEGER,
    job_name VARCHAR(255),
    data_source VARCHAR(100),
    table_name VARCHAR(100),
    record_type VARCHAR(100),
    status VARCHAR(20),
    total_estimated INTEGER,
    processed_records INTEGER,
    failed_records INTEGER,
    progress_percent NUMERIC,
    throughput_per_minute NUMERIC,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ij.id,
        ij.job_name,
        ij.data_source,
        ij.table_name,
        ij.record_type,
        ij.status,
        ij.total_estimated,
        ij.processed_records,
        ij.failed_records,
        CASE 
            WHEN ij.total_estimated > 0 
            THEN ROUND(ij.processed_records::NUMERIC / ij.total_estimated * 100, 2)
            ELSE 0
        END as progress_percent,
        ij.throughput_per_minute,
        ij.started_at,
        ij.completed_at,
        ij.metadata
    FROM ingestion.ingestion_jobs ij
    WHERE ij.id = p_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get active jobs
CREATE OR REPLACE FUNCTION ingestion.get_active_jobs()
RETURNS TABLE (
    id INTEGER,
    job_name VARCHAR(255),
    data_source VARCHAR(100),
    table_name VARCHAR(100),
    status VARCHAR(20),
    progress_percent NUMERIC,
    throughput_per_minute NUMERIC,
    minutes_running NUMERIC,
    started_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ij.id,
        ij.job_name,
        ij.data_source,
        ij.table_name,
        ij.status,
        CASE 
            WHEN ij.total_estimated > 0 
            THEN ROUND(ij.processed_records::NUMERIC / ij.total_estimated * 100, 2)
            ELSE 0
        END as progress_percent,
        ij.throughput_per_minute,
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ij.started_at))/60 as minutes_running,
        ij.started_at
    FROM ingestion.ingestion_jobs ij
    WHERE ij.status IN ('running', 'paused')
    ORDER BY ij.started_at DESC;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Congress Members Ingestion Functions
-- =============================================

-- Function to normalize Congress member data
CREATE OR REPLACE FUNCTION ingestion.normalize_congress_member(
    p_member_data JSONB
)
RETURNS ingestion.congress_member_type AS $$
DECLARE
    v_result ingestion.congress_member_type;
    v_name TEXT;
    v_name_parts TEXT[];
BEGIN
    -- Extract name parts
    v_name := p_member_data->>'name';
    v_name_parts := string_to_array(v_name, ' ');
    
    v_result.bioguide_id := p_member_data->>'bioguideId';
    v_result.first_name := COALESCE(p_member_data->>'firstName', v_name_parts[1]);
    v_result.last_name := COALESCE(p_member_data->>'lastName', v_name_parts[array_length(v_name_parts, 1)]);
    v_result.middle_name := p_member_data->>'middleName';
    v_result.suffix := p_member_data->>'suffix';
    v_result.official_full_name := v_name;
    v_result.birthday := p_member_data->>'birthDate';
    v_result.gender := p_member_data->>'gender';
    v_result.biography := COALESCE(p_member_data->>'biography', '');
    v_result.birthplace := p_member_data->>'birthPlace';
    v_result.death_date := p_member_data->>'deathDate';
    
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error normalizing member data: %', SQLERRM;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to upsert Congress members
CREATE OR REPLACE FUNCTION ingestion.upsert_congress_members(
    p_members JSONB
)
RETURNS INTEGER AS $$
DECLARE
    v_member JSONB;
    v_normalized ingestion.congress_member_type;
    v_count INTEGER := 0;
BEGIN
    FOR v_member IN SELECT * FROM jsonb_array_elements(p_members)
    LOOP
        BEGIN
            v_normalized := ingestion.normalize_congress_member(v_member);
            
            IF v_normalized IS NOT NULL THEN
                INSERT INTO congress.members (
                    bioguide_id, first_name, middle_name, last_name, suffix,
                    official_full_name, birthday, gender, biography, birthplace,
                    death_date, created_at, updated_at
                ) VALUES (
                    v_normalized.bioguide_id, v_normalized.first_name, v_normalized.middle_name,
                    v_normalized.last_name, v_normalized.suffix, v_normalized.official_full_name,
                    v_normalized.birthday, v_normalized.gender, v_normalized.biography,
                    v_normalized.birthplace, v_normalized.death_date,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (bioguide_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    middle_name = EXCLUDED.middle_name,
                    last_name = EXCLUDED.last_name,
                    suffix = EXCLUDED.suffix,
                    official_full_name = EXCLUDED.official_full_name,
                    birthday = EXCLUDED.birthday,
                    gender = EXCLUDED.gender,
                    biography = EXCLUDED.biography,
                    birthplace = EXCLUDED.birthplace,
                    death_date = EXCLUDED.death_date,
                    updated_at = CURRENT_TIMESTAMP;
                
                v_count := v_count + 1;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Error processing member %: %', v_member->>'bioguideId', SQLERRM;
        END;
    END LOOP;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- GovInfo Members Ingestion Functions
-- =============================================

-- Function to normalize GovInfo member data
CREATE OR REPLACE FUNCTION ingestion.normalize_govinfo_member(
    p_member_data JSONB
)
RETURNS ingestion.govinfo_member_type AS $$
DECLARE
    v_result ingestion.govinfo_member_type;
    v_name JSONB;
BEGIN
    v_name := p_member_data->'name';
    
    v_result.member_id := p_member_data->>'memberId';
    v_result.bioguide_id := p_member_data->>'bioguideId';
    v_result.first_name := COALESCE(v_name->>'first', v_name->>'givenName', '');
    v_result.middle_name := COALESCE(v_name->>'middle', '');
    v_result.last_name := COALESCE(v_name->>'last', v_name->>'familyName', '');
    v_result.suffix := COALESCE(v_name->>'suffix', '');
    v_result.full_name := COALESCE(v_name->>'fullName', 
        COALESCE(v_result.first_name || ' ' || v_result.last_name, ''));
    v_result.preferred_name := COALESCE(v_name->>'preferredName', '');
    v_result.birthday := ingestion.parse_date(p_member_data->>'birthDate');
    v_result.gender := p_member_data->>'gender';
    v_result.party_code := p_member_data->>'party';
    v_result.state := p_member_data->>'state';
    v_result.district := COALESCE(p_member_data->>'district', '');
    v_result.url := p_member_data->>'url';
    v_result.twitter_handle := p_member_data->>'twitter';
    v_result.youtube_handle := p_member_data->>'youtube';
    v_result.facebook_handle := p_member_data->>'facebook';
    v_result.biography_text := COALESCE(p_member_data->>'biography', p_member_data->>'bio', '');
    v_result.photo_url := p_member_data->>'photoUrl';
    
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error normalizing GovInfo member data: %', SQLERRM;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to upsert GovInfo members
CREATE OR REPLACE FUNCTION ingestion.upsert_govinfo_members(
    p_members JSONB
)
RETURNS INTEGER AS $$
DECLARE
    v_member JSONB;
    v_normalized ingestion.govinfo_member_type;
    v_count INTEGER := 0;
BEGIN
    FOR v_member IN SELECT * FROM jsonb_array_elements(p_members)
    LOOP
        BEGIN
            v_normalized := ingestion.normalize_govinfo_member(v_member);
            
            IF v_normalized IS NOT NULL THEN
                INSERT INTO govinfo.members (
                    member_id, bioguide_id, first_name, middle_name, last_name, suffix,
                    full_name, preferred_name, birthday, gender, party_code, state,
                    district, url, twitter_handle, youtube_handle, facebook_handle,
                    biography_text, photo_url, created_at, updated_at
                ) VALUES (
                    v_normalized.member_id, v_normalized.bioguide_id, v_normalized.first_name,
                    v_normalized.middle_name, v_normalized.last_name, v_normalized.suffix,
                    v_normalized.full_name, v_normalized.preferred_name, v_normalized.birthday,
                    v_normalized.gender, v_normalized.party_code, v_normalized.state,
                    v_normalized.district, v_normalized.url, v_normalized.twitter_handle,
                    v_normalized.youtube_handle, v_normalized.facebook_handle,
                    v_normalized.biography_text, v_normalized.photo_url,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (bioguide_id) DO UPDATE SET
                    member_id = EXCLUDED.member_id,
                    first_name = EXCLUDED.first_name,
                    middle_name = EXCLUDED.middle_name,
                    last_name = EXCLUDED.last_name,
                    suffix = EXCLUDED.suffix,
                    full_name = EXCLUDED.full_name,
                    preferred_name = EXCLUDED.preferred_name,
                    birthday = EXCLUDED.birthday,
                    gender = EXCLUDED.gender,
                    party_code = EXCLUDED.party_code,
                    state = EXCLUDED.state,
                    district = EXCLUDED.district,
                    url = EXCLUDED.url,
                    twitter_handle = EXCLUDED.twitter_handle,
                    youtube_handle = EXCLUDED.youtube_handle,
                    facebook_handle = EXCLUDED.facebook_handle,
                    biography_text = EXCLUDED.biography_text,
                    photo_url = EXCLUDED.photo_url,
                    updated_at = CURRENT_TIMESTAMP;
                
                v_count := v_count + 1;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Error processing GovInfo member %: %', v_member->>'memberId', SQLERRM;
        END;
    END LOOP;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- OpenStates People Ingestion Functions
-- =============================================

-- Function to normalize OpenStates person data
CREATE OR REPLACE FUNCTION ingestion.normalize_openstates_person(
    p_person_data JSONB
)
RETURNS ingestion.openstates_person_type AS $$
DECLARE
    v_result ingestion.openstates_person_type;
    v_jurisdiction JSONB;
BEGIN
    v_jurisdiction := p_person_data->'jurisdiction';
    
    v_result.person_id := p_person_data->>'id';
    v_result.name := p_person_data->>'name';
    v_result.family_name := p_person_data->>'familyName';
    v_result.given_name := p_person_data->>'givenName';
    v_result.image := p_person_data->>'image';
    v_result.gender := p_person_data->>'gender';
    v_result.biography := p_person_data->>'biography';
    v_result.birth_date := ingestion.parse_date(p_person_data->>'birthDate');
    v_result.death_date := ingestion.parse_date(p_person_data->>'deathDate');
    v_result.primary_party := COALESCE(p_person_data->>'primaryParty', p_person_data->>'party', '');
    v_result.jurisdiction_id := COALESCE(v_jurisdiction->>'id', '');
    v_result.current_role_data := p_person_data->'currentRole';
    
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error normalizing OpenStates person data: %', SQLERRM;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to upsert OpenStates people
CREATE OR REPLACE FUNCTION ingestion.upsert_openstates_people(
    p_people JSONB
)
RETURNS INTEGER AS $$
DECLARE
    v_person JSONB;
    v_normalized ingestion.openstates_person_type;
    v_count INTEGER := 0;
BEGIN
    FOR v_person IN SELECT * FROM jsonb_array_elements(p_people)
    LOOP
        BEGIN
            v_normalized := ingestion.normalize_openstates_person(v_person);
            
            IF v_normalized IS NOT NULL THEN
                INSERT INTO openstates.people (
                    person_id, name, family_name, given_name, image, gender, biography,
                    birth_date, death_date, primary_party, jurisdiction_id,
                    current_role_data, created_at, updated_at
                ) VALUES (
                    v_normalized.person_id, v_normalized.name, v_normalized.family_name,
                    v_normalized.given_name, v_normalized.image, v_normalized.gender,
                    v_normalized.biography, v_normalized.birth_date, v_normalized.death_date,
                    v_normalized.primary_party, v_normalized.jurisdiction_id,
                    v_normalized.current_role_data, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (person_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    family_name = EXCLUDED.family_name,
                    given_name = EXCLUDED.given_name,
                    image = EXCLUDED.image,
                    gender = EXCLUDED.gender,
                    biography = EXCLUDED.biography,
                    birth_date = EXCLUDED.birth_date,
                    death_date = EXCLUDED.death_date,
                    primary_party = EXCLUDED.primary_party,
                    jurisdiction_id = EXCLUDED.jurisdiction_id,
                    current_role_data = EXCLUDED.current_role_data,
                    updated_at = CURRENT_TIMESTAMP;
                
                v_count := v_count + 1;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Error processing OpenStates person %: %', v_person->>'id', SQLERRM;
        END;
    END LOOP;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Utility Functions
-- =============================================

-- Date parsing function
CREATE OR REPLACE FUNCTION ingestion.parse_date(p_date_text TEXT)
RETURNS TEXT AS $$
BEGIN
    IF p_date_text IS NULL OR p_date_text = '' THEN
        RETURN NULL;
    END IF;
    
    -- Try common date formats
    BEGIN
        RETURN to_char(p_date_text::DATE, 'YYYY-MM-DD');
    EXCEPTION WHEN OTHERS THEN
        -- Try other formats or return NULL
        RETURN NULL;
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to validate deduplication
CREATE OR REPLACE FUNCTION ingestion.validate_deduplication()
RETURNS TABLE (
    schema_name TEXT,
    table_name TEXT,
    total_records BIGINT,
    duplicate_count BIGINT,
    deduplication_status TEXT
) AS $$
BEGIN
    -- Congress members
    RETURN QUERY
    SELECT 
        'congress' as schema_name,
        'members' as table_name,
        COUNT(*) as total_records,
        COUNT(*) - COUNT(DISTINCT bioguide_id) as duplicate_count,
        CASE 
            WHEN COUNT(*) = COUNT(DISTINCT bioguide_id) THEN 'OK'
            ELSE 'DUPLICATES_FOUND'
        END as deduplication_status
    FROM congress.members;
    
    -- GovInfo members
    RETURN QUERY
    SELECT 
        'govinfo' as schema_name,
        'members' as table_name,
        COUNT(*) as total_records,
        COUNT(*) - COUNT(DISTINCT member_id) as duplicate_count,
        CASE 
            WHEN COUNT(*) = COUNT(DISTINCT member_id) THEN 'OK'
            ELSE 'DUPLICATES_FOUND'
        END as deduplication_status
    FROM govinfo.members;
    
    -- OpenStates people
    RETURN QUERY
    SELECT 
        'openstates' as schema_name,
        'people' as table_name,
        COUNT(*) as total_records,
        COUNT(*) - COUNT(DISTINCT person_id) as duplicate_count,
        CASE 
            WHEN COUNT(*) = COUNT(DISTINCT person_id) THEN 'OK'
            ELSE 'DUPLICATES_FOUND'
        END as deduplication_status
    FROM openstates.people;
END;
$$ LANGUAGE plpgsql;

-- Function to get ingestion statistics
CREATE OR REPLACE FUNCTION ingestion.get_ingestion_statistics()
RETURNS TABLE (
    data_source TEXT,
    total_records BIGINT,
    last_ingestion TIMESTAMP WITH TIME ZONE,
    ingestion_status TEXT,
    error_count BIGINT
) AS $$
BEGIN
    -- Congress
    RETURN QUERY
    SELECT 
        'congress.gov' as data_source,
        COUNT(*) as total_records,
        MAX(updated_at) as last_ingestion,
        'completed' as ingestion_status,
        0 as error_count
    FROM congress.members;
    
    -- GovInfo
    RETURN QUERY
    SELECT 
        'govinfo.gov' as data_source,
        COUNT(*) as total_records,
        MAX(updated_at) as last_ingestion,
        'completed' as ingestion_status,
        0 as error_count
    FROM govinfo.members;
    
    -- OpenStates
    RETURN QUERY
    SELECT 
        'openstates.org' as data_source,
        COUNT(*) as total_records,
        MAX(updated_at) as last_ingestion,
        'completed' as ingestion_status,
        0 as error_count
    FROM openstates.people;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Grant Permissions
-- =============================================

GRANT USAGE ON SCHEMA ingestion TO PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA ingestion TO PUBLIC;
GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA ingestion TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA ingestion TO PUBLIC;

COMMENT ON SCHEMA ingestion IS 'Complete ingestion system with monitoring and deduplication';