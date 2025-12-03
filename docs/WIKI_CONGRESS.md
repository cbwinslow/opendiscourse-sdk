# Congress.gov Data Source Documentation

## Overview
**Source**: [api.congress.gov](https://api.congress.gov/v3)
**API Key Required**: `CONGRESS_API_KEY`
**Coverage**: Congressional members, voting records, biographical data, bills, amendments
**Primary Schema**: `congress`
**Primary Ingestion Script**: `scripts/ingest_congress_incremental.py`

## Programming Language
**Primary Language**: Python
**Key Libraries**: `requests`, `psycopg2`, `python-dotenv`, `hashlib`
**Database System**: PostgreSQL with `pgcrypto` extension for UUID generation
**Additional Tools**: Rate limiting with exponential backoff

## API Endpoints

### Members API
```
GET /member/congress/{congress_number}
```
- **Description**: Get list of all members for a specific congress
- **Parameters**:
  - `limit`: Number of results per page (default: 50, max: 250)
  - `offset`: Pagination offset for results
  - `api_key`: Required API key

```
GET /member/{bioguide_id}/
```
- **Description**: Get detailed information for specific member
- **Response**: Biographical data, terms, roles, contact info

```
GET /member/{bioguide_id}/votes
```
- **Description**: Get voting record for specific member
- **Parameters**:
  - `congress`: Filter by congress number
  - `limit`: Results per page
  - `offset`: Pagination offset

### Bills API
```
GET /bill/congress/{congress_number}/
```
- **Description**: Get list of bills for specific congress
- **Parameters**:
  - `limit`: Results per page
  - `offset`: Pagination offset
  - `fromDate`, `toDate`: Date range filtering

```
GET /bill/congress/{congress_number}/{bill_type}/{bill_number}
```
- **Description**: Get detailed bill information including actions and summaries

### Committees API
```
GET /committee/congress/{congress_number}/
```
- **Description**: Get list of committees for congress
- **Parameters**:
  - `chamber`: Filter by 'house' or 'senate'
  - `type`: Filter by committee type

## SQL Data Model

### Core Tables (migrations/001_congress_schema.sql)

#### Reference Tables
```sql
-- Congress sessions with date ranges
CREATE TABLE congress.sessions (
    congress_number      integer PRIMARY KEY,
    start_date           date NOT NULL,
    end_date             date,
    odd_year             integer NOT NULL,
    even_year            integer NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Congressional chambers
CREATE TABLE congress.chambers (
    chamber_code         text PRIMARY KEY,
    name                 text NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

INSERT INTO congress.chambers (chamber_code, name) VALUES
    ('house', 'House of Representatives'),
    ('senate', 'Senate'),
    ('joint', 'Joint Session');

-- State information
CREATE TABLE congress.states (
    state_code           text PRIMARY KEY,
    name                 text NOT NULL,
    fips_code            text,
    is_territory         boolean NOT NULL DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Political parties
CREATE TABLE congress.parties (
    party_code           text PRIMARY KEY,
    display_name         text NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Document Storage
```sql
-- Document storage for full-text search
CREATE TABLE congress.documents (
    document_hash        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url           text NOT NULL,
    content_type         text,
    content_length       bigint,
    sha1_hash            text,
    title                text,
    description          text,
    published_at         timestamptz,
    retrieved_at         timestamptz NOT NULL DEFAULT now(),
    -- Full-text search vector
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Member Data Tables
```sql
-- Members with biographical information
CREATE TABLE congress.members (
    bioguide_id          text PRIMARY KEY,
    first_name           text NOT NULL,
    middle_name          text,
    last_name            text NOT NULL,
    suffix               text,
    official_full_name   text,
    birthday             date,
    gender               text,
    biography            text,
    birthplace           text,
    death_date           date,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Member terms in office
CREATE TABLE congress.member_terms (
    term_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bioguide_id          text NOT NULL REFERENCES congress.members (bioguide_id) ON DELETE CASCADE,
    congress_number      integer NOT NULL REFERENCES congress.sessions (congress_number) ON DELETE CASCADE,
    chamber_code         text NOT NULL REFERENCES congress.chambers (chamber_code),
    state_code           text REFERENCES congress.states (state_code),
    district             text,
    party_code           text REFERENCES congress.parties (party_code),
    start_date           date NOT NULL,
    end_date             date,
    role_title           text,
    leadership_role      text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Committee Tables
```sql
-- Committee information
CREATE TABLE congress.committees (
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

-- Committee membership
CREATE TABLE congress.committee_members (
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
```

#### Bills and Legislative Tables
```sql
-- Bill information
CREATE TABLE congress.bills (
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
    -- Full-text search vector
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(official_title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(summary_text, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (congress_number, bill_type, bill_number)
);

-- Bill titles
CREATE TABLE congress.bill_titles (
    bill_title_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    title_type           text NOT NULL,
    title                text NOT NULL,
    is_for_portion       boolean NOT NULL DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Bill actions timeline
CREATE TABLE congress.bill_actions (
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

-- Bill subjects and classifications
CREATE TABLE congress.bill_subjects (
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    subject_term         text NOT NULL,
    is_major             boolean NOT NULL DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (bill_id, subject_term)
);

-- Bill cosponsors
CREATE TABLE congress.bill_cosponsors (
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    bioguide_id          text NOT NULL REFERENCES congress.members (bioguide_id) ON DELETE CASCADE,
    cosponsored_date     date,
    is_original_cosponsor boolean DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (bill_id, bioguide_id)
);

-- Related bills
CREATE TABLE congress.related_bills (
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    related_bill_type    text NOT NULL,
    related_bill_number  integer NOT NULL,
    related_congress     integer NOT NULL,
    relationship_type    text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (bill_id, related_bill_type, related_bill_number, related_congress)
);

-- Bill text versions
CREATE TABLE congress.bill_text_versions (
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

-- Bill summaries
CREATE TABLE congress.bill_summaries (
    bill_summary_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              uuid NOT NULL REFERENCES congress.bills (bill_id) ON DELETE CASCADE,
    summary_date         date NOT NULL,
    summary_text         text NOT NULL,
    version_code         text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Amendment Tables
```sql
-- Amendments
CREATE TABLE congress.amendments (
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

-- Amendment actions
CREATE TABLE congress.amendment_actions (
    amendment_action_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    amendment_id         uuid NOT NULL REFERENCES congress.amendments (amendment_id) ON DELETE CASCADE,
    action_date          date NOT NULL,
    action_text          text NOT NULL,
    chamber_code         text REFERENCES congress.chambers (chamber_code),
    action_code          text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Amendment sponsors
CREATE TABLE congress.amendment_sponsors (
    amendment_id         uuid NOT NULL REFERENCES congress.amendments (amendment_id) ON DELETE CASCADE,
    bioguide_id          text NOT NULL REFERENCES congress.members (bioguide_id) ON DELETE CASCADE,
    sponsor_type         text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (amendment_id, bioguide_id, sponsor_type)
);
```

#### Indexes for Performance
```sql
-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_member_terms_member ON congress.member_terms (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_member_terms_congress ON congress.member_terms (congress_number);
CREATE INDEX IF NOT EXISTS idx_committee_members_committee ON congress.committee_members (committee_id);
CREATE INDEX IF NOT EXISTS idx_bills_congress_type ON congress.bills (congress_number, bill_type);
CREATE INDEX IF NOT EXISTS idx_bills_search_document ON congress.bills USING GIN (search_document);
CREATE INDEX IF NOT EXISTS idx_bill_actions_bill ON congress.bill_actions (bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_actions_date ON congress.bill_actions (action_date);
CREATE INDEX IF NOT EXISTS idx_documents_search ON congress.documents USING GIN (search_document);
```

## SQL Functions and Procedures

### Incremental Ingestion Functions
```sql
-- Core checkpoint management
SELECT incremental.get_or_create_checkpoint('congress.gov', 'members', '118', NULL);
SELECT incremental.update_checkpoint_progress(
    'congress.gov', 'members', '118',
    last_offset, NULL, NULL, NULL,
    records_processed, is_completed
);

-- Duplicate detection using SHA-256 fingerprinting
SELECT incremental.is_record_processed(
    'congress.gov', 'members', bioguide_id, member_data::jsonb
);

-- Session tracking
CALL incremental.start_ingestion_session(
    'congress_members_118_20250101_120000',
    'congress.gov',
    'members',
    '{"congress": 118, "batch_size": 50}'
);
CALL incremental.complete_ingestion_session(session_id, 'completed', NULL);
```

### Data Verification Functions (migrations/006_member_verification_functions.sql)
```sql
-- Member count by congress
SELECT congress.get_member_count_by_congress(118);

-- Unique member count across all congresses
SELECT congress.get_unique_member_count();

-- Total member terms count
SELECT congress.get_total_member_terms_count();

-- Longest serving members
SELECT * FROM congress.get_longest_serving_members(10);

-- Party distribution for specific congress
SELECT * FROM congress.get_party_distribution(118);

-- Chamber distribution
SELECT * FROM congress.get_chamber_distribution(118);

-- State representation
SELECT * FROM congress.get_state_representation(118, 'house');

-- Data completeness check
SELECT * FROM congress.check_member_data_completeness();

-- Member career path
SELECT * FROM congress.get_member_career_path('S000001');

-- Congress summary statistics
SELECT * FROM congress.get_congress_summary(118);
```

### Data Verification Procedures (migrations/005_member_verification_procedures.sql)
```sql
-- Comprehensive member statistics
CALL congress.get_member_statistics(118);

-- Data quality checks
CALL congress.check_data_quality();

-- Clean duplicate terms
CALL congress.clean_duplicate_terms();

-- Member career summary
CALL congress.get_member_career_summary('S000001');
```

## Python Ingestion Functions

### Primary Class: IncrementalCongressIngestor

#### Core Methods
```python
class IncrementalCongressIngestor:
    def __init__(self):
        # Initialize API key validation
        # Setup base URL, batch size, database connection
        # Validate CONGRESS_API_KEY environment variable
        # Enable production mode enforcement

    def get_next_ingestion_params(self, congress: int) -> Dict[str, Any]:
        """Get next ingestion parameters from checkpoint for resuming"""

    def create_checkpoint(self, congress: int, total_estimated: int = None):
        """Create or get checkpoint for this congress"""

    def update_checkpoint(self, congress: int, last_offset: int,
                          records_processed: int = 0, is_completed: bool = False,
                          total_estimated: int = None, set_total_processed: int = None):
        """Update checkpoint progress with completion handling"""

    def is_record_processed(self, member_id: str, member_data: Dict[str, Any]) -> bool:
        """Check if record already processed using SHA-256 fingerprinting"""
```

#### API Client Methods
```python
    def fetch_members_page(self, congress: int, offset: int = 0) -> Dict[str, Any]:
        """Fetch a page of members from Congress.gov API"""
        # Uses adaptive rate limiting
        # Handles pagination automatically
        # Applies exponential backoff for rate limits
        # Returns structured member data

    def normalize_member_data(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform API member data to database format"""
        # Extract name components from full name
        # Map API fields to database columns
        # Handle optional biographical information
        # Generate consistent data structures
```

#### Data Processing Methods
```python
    def insert_members_batch(self, members: List[Dict[str, Any]]) -> int:
        """Insert batch of members with UPSERT conflict handling"""
        # Use psycopg2.extras.execute_values for bulk insertion
        # Handle bioguide_id conflicts with ON CONFLICT
        # Return count of successfully inserted records
        # Maintain database transaction integrity
```

#### Session Management Methods
```python
    def start_ingestion_session(self, congress: int) -> str:
        """Start ingestion session with tracking"""
        # Generate unique session ID with timestamp
        # Log session start in incremental schema
        # Record initial session metadata

    def complete_ingestion_session(self, session_id: str, status: str = 'completed', error_summary: str = None):
        """Complete ingestion session with final status"""
        # Update session with completion status
        # Record final statistics and any errors
        # Ensure proper session closure
```

#### Main Ingestion Methods
```python
    def ingest_congress_members(self, congress: int) -> Dict[str, Any]:
        """Main method to ingest all members for specific congress"""
        # Check existing checkpoint for progress
        # Create checkpoint if needed
        # Start tracking session
        # Process paginated member data
        # Handle deduplication via fingerprinting
        # Update progress after each batch
        # Mark completion and finalize session

    def ingest_all_congresses(self, start_congress: int = 118, end_congress: int = 118):
        """Ingest multiple congresses sequentially"""
        # Loop through congress range
        # Handle individual congress failures gracefully
        # Provide comprehensive summary statistics
        # Return detailed results for each congress
```

### Configuration (config/member_api_config.py)
```python
# API configuration
API_KEY = os.getenv("CONGRESS_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.congress.gov/v3"
HEADERS = {"X-Api-Key": API_KEY, "Accept": "application/json"}

# Member endpoints
MEMBER_LIST_URL = f"{BASE_URL}/member"
MEMBER_DETAILS_URL = f"{BASE_URL}/member/{{member_id}}"
MEMBER_VOTES_URL = f"{BASE_URL}/member/{{member_id}}/votes"
MEMBER_DATA_DIR = "member_data"

# Create data directory
os.makedirs(MEMBER_DATA_DIR, exist_ok=True)
```

### API Key Validation and Enforcement
```python
# Key validation functions (ingestion_config.py)
def validate_all_api_keys() -> Dict[str, Any]:
    """Validate all required API keys before ingestion"""

def get_api_key_from_env(key_name: str) -> str:
    """Get and validate specific API key"""

def get_ingestion_mode_from_env() -> IngestionMode:
    """Determine ingestion mode (production/enforcement)"""

# Production mode enforcement
def validate_and_start_ingestion(api_key: str, base_url: str, mode: IngestionMode) -> bool:
    """Validate API configuration before starting ingestion"""
```

### Key Ingestion Flow
1. **API Key Validation**: Verify `CONGRESS_API_KEY` environment variable
2. **Production Mode Check**: Ensure production mode is enabled
3. **Checkpoint Resume**: Continue from last processed offset
4. **Paginated Fetch**: Get member data in configurable batches
5. **Data Normalization**: Transform API format to database schema
6. **Duplicate Detection**: Use SHA-256 fingerprinting to avoid reprocessing
7. **Bulk Insertion**: UPSERT members with conflict handling
8. **Progress Tracking**: Update checkpoints after each batch
9. **Session Completion**: Log final status and statistics

### Rate Limiting and Error Handling
- **Adaptive Rate Limiting**: Monitor API response headers for quota limits
- **Exponential Backoff**: Handle 429 rate limit errors with progressive delays
- **Retry Logic**: 3 attempts with increasing backoff intervals
- **Database Transactions**: Automatic rollback on failures
- **Comprehensive Logging**: Track all operations, errors, and progress
- **Production Enforcement**: Reject demo/placeholder keys immediately

### Performance Characteristics
- **Batch Size**: Configurable (default: 50 members per batch)
- **Processing Speed**: ~50 records per batch with full validation
- **API Response Time**: <2 seconds average response time
- **Database Operations**: Optimized batch UPSERT operations
- **Memory Usage**: Streaming processing to handle large datasets
- **Resume Capability**: Checkpoint-based recovery for interrupted processes