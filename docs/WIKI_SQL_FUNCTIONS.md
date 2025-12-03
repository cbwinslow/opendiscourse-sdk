# SQL Functions and Procedures Documentation

## Overview
This document provides comprehensive documentation for all SQL functions and procedures used in the Open Discourse project for data ingestion, verification, and analysis.

## Database Schemas

### 1. Incremental Schema (migrations/014_incremental_ingestion_tracking.sql)
**Purpose**: Tracks ingestion progress, checkpoints, and session management across all data sources.

### 2. Congress Schema (migrations/001_congress_schema.sql)
**Purpose**: Federal congressional data including members, bills, votes, and committees.

### 3. GovInfo Schema (migrations/002_govinfo_schema.sql)
**Purpose**: Government documents and publications data.

### 4. OpenStates Schema (migrations/003_openstates_schema_optimized.sql)
**Purpose**: State legislative data across all US jurisdictions.

## Incremental Schema Functions and Procedures

### Core Checkpoint Management

#### `incremental.get_or_create_checkpoint()`
```sql
FUNCTION incremental.get_or_create_checkpoint(
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_category VARCHAR(100),
    p_total_estimated INTEGER DEFAULT NULL
)
RETURNS incremental.ingestion_checkpoints
```
**Purpose**: Get existing checkpoint or create new one for resuming ingestion
**Parameters**:
- `p_data_source`: Data source name (congress.gov, govinfo.gov, openstates.org)
- `p_data_type`: Type of data (members, bills, votes, etc.)
- `p_category`: Category identifier (congress number, state code, etc.)
- `p_total_estimated`: Estimated total records to process

**Returns**: Complete checkpoint record with current progress

**Example**:
```sql
SELECT * FROM incremental.get_or_create_checkpoint('congress.gov', 'members', '118', 554);
```

#### `incremental.update_checkpoint_progress()`
```sql
FUNCTION incremental.update_checkpoint_progress(
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_category VARCHAR(100),
    p_last_offset INTEGER DEFAULT NULL,
    p_last_page INTEGER DEFAULT NULL,
    p_last_id VARCHAR(500) DEFAULT NULL,
    p_last_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_records_processed INTEGER DEFAULT 0,
    p_is_completed BOOLEAN DEFAULT FALSE
)
RETURNS VOID
```
**Purpose**: Update checkpoint progress after processing records
**Parameters**:
- Progress tracking parameters (offset, page, ID, timestamp)
- Processing statistics (records processed, completion status)

**Example**:
```sql
CALL incremental.update_checkpoint_progress(
    'congress.gov', 'members', '118',
    150, 3, 'M001', NULL,
    50, FALSE
);
```

#### `incremental.is_record_processed()`
```sql
FUNCTION incremental.is_record_processed(
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_record_id VARCHAR(500),
    p_record_content JSONB DEFAULT NULL
)
RETURNS BOOLEAN
```
**Purpose**: Check if record was already processed using SHA-256 fingerprinting
**Parameters**:
- Source identification
- Record identifier and content for fingerprinting
- Optional content hash for change detection

**Returns**: Boolean indicating if record was processed (true) or needs processing (false)

**Example**:
```sql
SELECT incremental.is_record_processed(
    'congress.gov', 'members', 'S000001',
    '{"bioguideId": "S000001", "name": "John Smith"}'::jsonb
);
```

### Session Management

#### `incremental.start_ingestion_session()`
```sql
FUNCTION incremental.start_ingestion_session(
    p_session_id VARCHAR(100),
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_session_metadata JSONB DEFAULT '{}'
)
RETURNS VOID
```
**Purpose**: Start tracking ingestion session with metadata
**Parameters**:
- Unique session identifier
- Source and data type information
- Additional session metadata as JSON

**Example**:
```sql
CALL incremental.start_ingestion_session(
    'congress_members_118_20250101_120000',
    'congress.gov',
    'members',
    '{"congress": 118, "batch_size": 50, "started_by": "script"}'::jsonb
);
```

#### `incremental.complete_ingestion_session()`
```sql
FUNCTION incremental.complete_ingestion_session(
    p_session_id VARCHAR(100),
    p_status VARCHAR(20) DEFAULT 'completed',
    p_error_summary TEXT DEFAULT NULL
)
RETURNS VOID
```
**Purpose**: Complete ingestion session with final status and summary
**Parameters**:
- Session identifier
- Completion status (completed, failed, paused)
- Optional error summary

**Example**:
```sql
CALL incremental.complete_ingestion_session(
    'congress_members_118_20250101_120000',
    'completed',
    'Successfully processed 554 members across all congresses'
);
```

#### `incremental.get_next_ingestion_params()`
```sql
FUNCTION incremental.get_next_ingestion_params(
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_category VARCHAR(100)
)
RETURNS TABLE(
    next_offset INTEGER,
    next_page INTEGER,
    start_from_id VARCHAR(500),
    start_from_timestamp TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN
)
```
**Purpose**: Get parameters for resuming ingestion from checkpoint
**Parameters**:
- Source, type, and category identification

**Returns**: Table with next ingestion parameters (offset, page, ID, timestamp, completion status)

**Example**:
```sql
SELECT * FROM incremental.get_next_ingestion_params(
    'congress.gov', 'members', '118'
);
```

### Status Monitoring

#### `incremental.checkpoint_status` (View)
```sql
CREATE OR REPLACE VIEW incremental.checkpoint_status AS
SELECT
    data_source,
    data_type,
    category,
    last_offset,
    last_page,
    last_id,
    is_completed,
    total_processed,
    total_estimated,
    completion_percentage,
    last_ingestion_at,
    error_count,
    CASE
        WHEN is_completed THEN '✅ COMPLETED'
        WHEN completion_percentage > 0 THEN '🔄 IN PROGRESS'
        WHEN error_count > 0 THEN '❌ ERROR'
        ELSE '📋 NOT STARTED'
    END as status
FROM incremental.ingestion_checkpoints
ORDER BY data_source, data_type, category;
```
**Purpose**: Monitor status of all ingestion checkpoints
**Usage**: View all checkpoint progress with formatted status indicators

**Example**:
```sql
SELECT * FROM incremental.checkpoint_status
WHERE data_source = 'congress.gov';
```

## Congress Schema Functions

### Member Analysis Functions

#### `congress.get_member_count_by_congress()`
```sql
FUNCTION congress.get_member_count_by_congress(p_congress_number INTEGER)
RETURNS INTEGER
```
**Purpose**: Get total member count for specific congress
**Parameters**: Congress number to analyze

**Example**:
```sql
SELECT congress.get_member_count_by_congress(118);
-- Returns: 554 (total members in Congress 118)
```

#### `congress.get_unique_member_count()`
```sql
FUNCTION congress.get_unique_member_count()
RETURNS INTEGER
```
**Purpose**: Get count of unique members across all congresses

**Example**:
```sql
SELECT congress.get_unique_member_count();
-- Returns: 1901 (total unique members ever served)
```

#### `congress.get_longest_serving_members()`
```sql
FUNCTION congress.get_longest_serving_members(p_limit INTEGER DEFAULT 10)
RETURNS TABLE (
    bioguide_id TEXT,
    first_name TEXT,
    last_name TEXT,
    terms_served INTEGER,
    first_congress INTEGER,
    last_congress INTEGER
)
```
**Purpose**: Find members with most terms served
**Parameters**: Number of results to return

**Example**:
```sql
SELECT * FROM congress.get_longest_serving_members(5);
-- Returns top 5 longest-serving members with career details
```

#### `congress.get_party_distribution()`
```sql
FUNCTION congress.get_party_distribution(p_congress_number INTEGER)
RETURNS TABLE (
    party_code TEXT,
    party_name TEXT,
    member_count INTEGER,
    percentage NUMERIC
)
```
**Purpose**: Get party distribution for congress with percentages
**Parameters**: Congress number to analyze

**Example**:
```sql
SELECT * FROM congress.get_party_distribution(118);
-- Returns party breakdown: D-213 (48.2%), R-222 (50.3%), etc.
```

#### `congress.get_chamber_distribution()`
```sql
FUNCTION congress.get_chamber_distribution(p_congress_number INTEGER)
RETURNS TABLE (
    chamber_code TEXT,
    chamber_name TEXT,
    member_count INTEGER
)
```
**Purpose**: Get member count by chamber (House/Senate)
**Parameters**: Congress number to analyze

**Example**:
```sql
SELECT * FROM congress.get_chamber_distribution(118);
-- Returns: House-435, Senate-100, Joint-1
```

#### `congress.get_state_representation()`
```sql
FUNCTION congress.get_state_representation(
    p_congress_number INTEGER,
    p_chamber_code TEXT DEFAULT NULL
)
RETURNS TABLE (
    state_code TEXT,
    state_name TEXT,
    member_count INTEGER
)
```
**Purpose**: Get state representation count with optional chamber filter
**Parameters**: Congress number and optional chamber filter

**Example**:
```sql
-- All chambers
SELECT * FROM congress.get_state_representation(118);

-- House only
SELECT * FROM congress.get_state_representation(118, 'house');
```

### Data Quality Functions

#### `congress.check_member_data_completeness()`
```sql
FUNCTION congress.check_member_data_completeness()
RETURNS TABLE (
    check_type TEXT,
    issue_count INTEGER,
    percentage_issue NUMERIC
)
```
**Purpose**: Check completeness of member data across various fields
**Returns**: Table showing missing data counts and percentages

**Example**:
```sql
SELECT * FROM congress.check_member_data_completeness();
-- Returns: Missing birthdays: 45 (2.4%), Missing genders: 12 (0.6%), etc.
```

#### `congress.get_member_career_path()`
```sql
FUNCTION congress.get_member_career_path(p_bioguide_id TEXT)
RETURNS TABLE (
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
```
**Purpose**: Get complete career path for specific member
**Parameters**: Member's bioguide ID

**Example**:
```sql
SELECT * FROM congress.get_member_career_path('S000001');
-- Returns complete list of terms, chambers, states, parties for member
```

#### `congress.get_congress_summary()`
```sql
FUNCTION congress.get_congress_summary(p_congress_number INTEGER)
RETURNS TABLE (
    metric_name TEXT,
    metric_value TEXT
)
```
**Purpose**: Get comprehensive summary statistics for congress
**Parameters**: Congress number to analyze

**Example**:
```sql
SELECT * FROM congress.get_congress_summary(118);
-- Returns: Total Members: 554, House Members: 435, Senate Members: 100, etc.
```

## Congress Schema Procedures

### Member Statistics Procedures

#### `congress.get_member_statistics()`
```sql
PROCEDURE congress.get_member_statistics(IN p_congress_number INTEGER DEFAULT NULL)
```
**Purpose**: Get comprehensive member statistics for congress or overall
**Parameters**: Optional congress number (returns overall stats if NULL)

**Example**:
```sql
-- Specific congress
CALL congress.get_member_statistics(118);

-- Overall statistics
CALL congress.get_member_statistics();
```

#### `congress.check_data_quality()`
```sql
PROCEDURE congress.check_data_quality()
```
**Purpose**: Check for common data quality issues in member data

**Example**:
```sql
CALL congress.check_data_quality();
-- Reports: Missing birthdays: 45, Missing genders: 12, Duplicate terms: 3, etc.
```

#### `congress.clean_duplicate_terms()`
```sql
PROCEDURE congress.clean_duplicate_terms()
```
**Purpose**: Remove duplicate member terms, keeping first occurrence

**Example**:
```sql
CALL congress.clean_duplicate_terms();
-- Cleans duplicate terms and reports number removed
```

#### `congress.get_member_career_summary()`
```sql
PROCEDURE congress.get_member_career_summary(IN p_bioguide_id TEXT)
```
**Purpose**: Get career summary for specific member
**Parameters**: Member's bioguide ID

**Example**:
```sql
CALL congress.get_member_career_summary('S000001');
-- Reports: Career summary including terms, congress range, chambers, parties, states
```

## Database Indexes and Performance

### Performance Optimization Indexes

#### Congress Schema Indexes
```sql
-- Member performance indexes
CREATE INDEX idx_member_terms_member ON congress.member_terms (bioguide_id);
CREATE INDEX idx_member_terms_congress ON congress.member_terms (congress_number);

-- Committee performance indexes
CREATE INDEX idx_committee_members_committee ON congress.committee_members (committee_id);

-- Bill performance indexes
CREATE INDEX idx_bills_congress_type ON congress.bills (congress_number, bill_type);
CREATE INDEX idx_bills_search_document ON congress.bills USING GIN (search_document);

-- Action timeline indexes
CREATE INDEX idx_bill_actions_bill ON congress.bill_actions (bill_id);
CREATE INDEX idx_bill_actions_date ON congress.bill_actions (action_date);

-- Document search indexes
CREATE INDEX idx_documents_search ON congress.documents USING GIN (search_document);
```

#### OpenStates Schema Indexes
```sql
-- Jurisdiction indexes
CREATE INDEX idx_openstates_jurisdictions_state ON openstates.jurisdictions(state_code);
CREATE INDEX idx_openstates_jurisdictions_search ON openstates.jurisdictions USING GIN (search_document);

-- People indexes
CREATE INDEX idx_openstates_people_jurisdiction ON openstates.people(jurisdiction_id);
CREATE INDEX idx_openstates_people_party ON openstates.people(primary_party);
CREATE INDEX idx_openstates_people_search ON openstates.people USING GIN (search_document);

-- Bill indexes
CREATE INDEX idx_openstates_bills_jurisdiction ON openstates.bills(jurisdiction_id);
CREATE INDEX idx_openstates_bills_session ON openstates.bills(session_id);
CREATE INDEX idx_openstates_bills_dates ON openstates.bills(latest_action_date, first_action_date);
CREATE INDEX idx_openstates_bills_search ON openstates.bills USING GIN (search_document);

-- Vote indexes
CREATE INDEX idx_openstates_vote_events_bill ON openstates.vote_events(bill_id);
CREATE INDEX idx_openstates_vote_events_org ON openstates.vote_events(organization_id);
CREATE INDEX idx_openstates_vote_events_date ON openstates.vote_events(start_date);
```

#### Incremental Schema Indexes
```sql
-- Checkpoint performance indexes
CREATE INDEX idx_ingestion_checkpoints_source_type ON incremental.ingestion_checkpoints(data_source, data_type);
CREATE INDEX idx_ingestion_checkpoints_category ON incremental.ingestion_checkpoints(category);
CREATE INDEX idx_ingestion_checkpoints_completed ON incremental.ingestion_checkpoints(is_completed);
CREATE INDEX idx_ingestion_checkpoints_last_ingestion ON incremental.ingestion_checkpoints(last_ingestion_at DESC);

-- Fingerprint indexes
CREATE INDEX idx_record_fingerprints_source_type ON incremental.record_fingerprints(data_source, data_type);
CREATE INDEX idx_record_fingerprints_record_id ON incremental.record_fingerprints(record_id);
CREATE INDEX idx_record_fingerprints_hash ON incremental.record_fingerprints(record_hash);
CREATE INDEX idx_record_fingerprints_last_updated ON incremental.record_fingerprints(last_updated_at DESC);

-- Session indexes
CREATE INDEX idx_ingestion_sessions_status ON incremental.ingestion_sessions(status);
CREATE INDEX idx_ingestion_sessions_started_at ON incremental.ingestion_sessions(started_at DESC);
```

## Usage Examples and Best Practices

### Monitoring Ingestion Progress
```sql
-- Check all active checkpoints
SELECT * FROM incremental.checkpoint_status
WHERE status LIKE '%IN PROGRESS%';

-- Check specific source progress
SELECT * FROM incremental.checkpoint_status
WHERE data_source = 'congress.gov'
ORDER BY last_ingestion_at DESC;
```

### Data Quality Assessment
```sql
-- Check data completeness across all sources
SELECT * FROM congress.check_member_data_completeness();

-- Get longest-serving members analysis
SELECT bioguide_id, first_name, last_name, terms_served
FROM congress.get_longest_serving_members(20)
WHERE terms_served > 10;
```

### Resume Interrupted Ingestion
```sql
-- Get next parameters for resuming
SELECT * FROM incremental.get_next_ingestion_params('congress.gov', 'members', '117');

-- Check if work is needed
SELECT CASE
    WHEN is_completed THEN 'Already completed'
    WHEN total_processed > 0 THEN 'Resume from offset: ' || next_offset
    ELSE 'Start fresh'
END as action_needed
FROM incremental.get_next_ingestion_params('congress.gov', 'members', '117');
```

### Audit and Troubleshooting
```sql
-- Check recent ingestion sessions
SELECT session_id, data_source, data_type, status, records_processed, started_at, completed_at
FROM incremental.ingestion_sessions
WHERE started_at > NOW() - INTERVAL '7 days'
ORDER BY started_at DESC;

-- Check for error patterns
SELECT data_source, data_type, COUNT(*) as error_count
FROM incremental.ingestion_sessions
WHERE status = 'failed'
AND started_at > NOW() - INTERVAL '30 days'
GROUP BY data_source, data_type
ORDER BY error_count DESC;
```
