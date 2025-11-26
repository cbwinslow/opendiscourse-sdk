# GovInfo Data Source Documentation

## Overview
**Source**: [api.govinfo.gov](https://api.govinfo.gov)
**API Key Required**: `GOVINFO_API_KEY`
**Coverage**: Federal legislation, congressional documents, committee information, voting records
**Primary Schema**: `govinfo`
**Primary Ingestion Script**: `scripts/ingest_govinfo_incremental.py`

## Programming Language
**Primary Language**: Python
**Key Libraries**: `requests`, `psycopg2`, `python-dotenv`, `hashlib`
**Database System**: PostgreSQL with `pgcrypto` extension

## API Endpoints

### Collections API
```
GET /collections/{collection_code}/2023-01-01T00:00:00Z
```
- **Description**: Retrieve Congressional Directory packages
- **Parameters**:
  - `api_key`: Required API key
  - `congress`: Congress number filter
  - `offset`: Pagination offset (default: 0)
  - `pageSize`: Results per page (default: 100)

### Package Content API
```
GET /packages/{package_id}/htm
```
- **Description**: Get download URLs for package content
- **Response**: JSON with download links for different formats (PDF, XML, TXT, HTML)

### Committee API
```
GET /browse/committee
GET /committees/{committee_code}
```
- **Description**: Browse committee information and details
- **Response**: Committee metadata and associated documents

## SQL Data Model

### Core Tables (migrations/002_govinfo_schema.sql)

#### Reference Tables
```sql
-- Document collections
CREATE TABLE govinfo.collections (
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

-- Congressional chambers
CREATE TABLE govinfo.chambers (
    chamber_code             text PRIMARY KEY,
    chamber_name             text NOT NULL,
    chamber_type             text,
    description              text
);

-- Congress sessions
CREATE TABLE govinfo.congresses (
    congress_number          integer PRIMARY KEY,
    start_date               date,
    end_date                 date,
    session_count            integer,
    description              text
);

-- Political parties
CREATE TABLE govinfo.parties (
    party_code               text PRIMARY KEY,
    party_name               text NOT NULL,
    ideology_score           numeric,
    notes                    text
);

-- Committee information
CREATE TABLE govinfo.committees (
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
```

#### Member Data Tables
```sql
-- Members with biographical information
CREATE TABLE govinfo.members (
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

-- Member terms in office
CREATE TABLE govinfo.member_terms (
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

-- Committee memberships
CREATE TABLE govinfo.memberships (
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
```

#### Document Management Tables
```sql
-- Package information
CREATE TABLE govinfo.packages (
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

-- Individual granules within packages
CREATE TABLE govinfo.granules (
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
```

#### Bills and Legislative Data Tables
```sql
-- Bill information
CREATE TABLE govinfo.bills (
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

-- Bill versions and summaries
CREATE TABLE govinfo.bill_versions (
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

CREATE TABLE govinfo.bill_summaries (
    bill_summary_id          bigserial PRIMARY KEY,
    bill_id                  text REFERENCES govinfo.bills(bill_id) ON DELETE CASCADE,
    summary_date             date,
    summary_text             text,
    source                   text,
    is_official              boolean,
    metadata                 jsonb,
    UNIQUE (bill_id, summary_date, source)
);

-- Bill actions and activities
CREATE TABLE govinfo.bill_actions (
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
```

#### Voting and Attendance Tables
```sql
-- Vote records
CREATE TABLE govinfo.votes (
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

-- Individual member votes
CREATE TABLE govinfo.vote_ballots (
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

-- Vote totals and results
CREATE TABLE govinfo.vote_totals (
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
```

## SQL Functions and Procedures

### Incremental Ingestion Functions (from incremental schema)
```sql
-- Checkpoint management
SELECT incremental.get_or_create_checkpoint('govinfo.gov', 'members', 'all', NULL);
SELECT incremental.update_checkpoint_progress(
    'govinfo.gov', 'members', 'all',
    last_offset, last_page, NULL, NULL,
    records_processed, is_completed
);

-- Duplicate detection
SELECT incremental.is_record_processed(
    'govinfo.gov', 'members', member_id, member_data::jsonb
);

-- Session management
CALL incremental.start_ingestion_session(session_id, 'govinfo.gov', 'members', '{}');
CALL incremental.complete_ingestion_session(session_id, 'completed', NULL);
```

## Python Ingestion Functions

### Primary Class: IncrementalGovInfoIngestor

#### Core Methods
```python
class IncrementalGovInfoIngestor:
    def __init__(self):
        # Initialize API key, base URL, batch size, database connection
        # Validate GOVINFO_API_KEY environment variable
        # Setup PostgreSQL connection

    def get_next_ingestion_params(self, congress: int = None) -> Dict[str, Any]:
        """Get next parameters from checkpoint for resuming ingestion"""

    def create_checkpoint(self, congress: int = None, total_estimated: int = None):
        """Create new checkpoint if none exists"""

    def update_checkpoint(self, congress: int = None, last_offset: int = None,
                         records_processed: int = 0, is_completed: bool = False):
        """Update progress in checkpoint"""

    def is_record_processed(self, member_id: str, member_data: Dict[str, Any]) -> bool:
        """Check if record already processed using SHA-256 fingerprinting"""
```

#### API Client Methods
```python
    def fetch_congressional_directories(self, congress: int) -> List[Dict[str, Any]]:
        """Fetch Congressional Directory packages for specific congress"""
        # Uses adaptive rate limiting
        # Handles 429 rate limit errors with exponential backoff

    def fetch_directory_content(self, package_id: str) -> str:
        """Fetch text content from Congressional Directory package"""
        # Get download URL from API
        # Fetch actual text content

    def parse_members_from_directory(self, content: str) -> List[Dict[str, Any]]:
        """Parse member information from Congressional Directory text"""
        # Basic pattern matching for Senate/House sections
        # Extract name, state, party information
```

#### Data Processing Methods
```python
    def normalize_member_data(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform API data to database format"""
        # Extract name components (first, middle, last, suffix)
        # Map API fields to database columns
        # Handle missing data gracefully

    def insert_members_batch(self, members: List[Dict[str, Any]]) -> int:
        """Insert batch of members with UPSERT handling"""
        # Use psycopg2.extras.execute_values for bulk insertion
        # Handle conflicts using ON CONFLICT (bioguide_id)
        # Return count of inserted records
```

#### Session Management Methods
```python
    def start_ingestion_session(self, congress: int = None) -> str:
        """Start new ingestion session with tracking"""
        # Generate unique session ID
        # Log session start in incremental.ingestion_sessions

    def complete_ingestion_session(self, session_id: str, status: str = 'completed', error_summary: str = None):
        """Complete ingestion session with final status"""
        # Update session status and completion time
        # Log any errors or summaries
```

#### Main Ingestion Methods
```python
    def ingest_congress_members(self, congress: int) -> Dict[str, Any]:
        """Main method to ingest members for specific congress"""
        # Check checkpoint for existing progress
        # Fetch and parse Congressional Directory
        # Process members with deduplication
        # Update progress and mark completion

    def ingest_all_congresses(self, start_congress: int = 118, end_congress: int = 118):
        """Ingest multiple congresses sequentially"""
        # Loop through congress range
        # Handle individual congress failures
        # Provide summary statistics
```

### Configuration (config/govinfo_config.py)
```python
# Collection types and metadata
class CollectionType:
    BILLS = "BILLS"
    CFR = "CFR"
    FEDERAL_REGISTER = "FR"
    COMMITTEE_HEARINGS = "CHRG"
    CONGRESSIONAL_RECORD = "CREC"
    HOUSE_DOCUMENTS = "HDOC"
    SENATE_DOCUMENTS = "SDOC"

# Processing configuration
PROCESSING_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1.0,
    "batch_size": 100,
    "timeout": 30,
    "schema_validation_enabled": True,
    "metadata_validation_enabled": True,
    "version_tracking_enabled": True,
}
```

### Key Ingestion Flow
1. **Environment Setup**: Load API key from `GOVINFO_API_KEY`
2. **Checkpoint Check**: Resume from last processed position
3. **Directory Fetch**: Get Congressional Directory packages
4. **Content Parse**: Extract member data from text
5. **Normalization**: Transform to database format
6. **Batch Insert**: UPSERT members with conflict handling
7. **Progress Update**: Record ingestion progress
8. **Session Complete**: Log final status

### Rate Limiting and Error Handling
- **Adaptive Rate Limiting**: Monitor API response headers
- **Exponential Backoff**: Handle 429 rate limit errors
- **Retry Logic**: 3 attempts with increasing delays
- **Database Transactions**: Rollback on failures
- **Comprehensive Logging**: Track all operations and errors
