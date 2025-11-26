
# OpenStates Data Source Documentation

## Overview
**Source**: [v3.openstates.org](https://v3.openstates.org)
**API Key Required**: `OPENSTATES_API_KEY`
**Coverage**: State legislature data across all US states (people, bills, votes, committees)
**Primary Schema**: `openstates`
**Primary Ingestion Script**: `scripts/ingest_openstates_incremental.py`

## Programming Language
**Primary Language**: Python
**Key Libraries**: `requests`, `psycopg2`, `python-dotenv`, `hashlib`, `json`
**Database System**: PostgreSQL with `pgcrypto` extension
**Standards**: Open Civic Data (OCD) compliance with normalized identifiers

## API Endpoints

### People API
```
GET /people
```
- **Description**: Get list of people (legislators) across all jurisdictions
- **Parameters**:
  - `apikey`: Required API key
  - `jurisdiction`: Filter by state/county (e.g., 'ca', 'tx', 'ny')
  - `per_page`: Results per page (max: 50)
  - `page`: Page number for pagination

```
GET /people/{person_id}
```
- **Description**: Get detailed information for specific person
- **Response**: Full profile with current role, contact info, identifiers

### Bills API
```
GET /bills
```
- **Description**: Get list of bills across all jurisdictions
- **Parameters**:
  - `apikey`: Required API key
  - `jurisdiction`: Filter by state
  - `session`: Filter by legislative session
  - `search`: Text search in bill titles
  - `per_page`, `page`: Pagination

### Votes API
```
GET /votes
```
- **Description**: Get voting records
- **Parameters**:
  - `apikey`: Required API key
  - `jurisdiction`: Filter by state
  - `bill`: Filter by specific bill
  - `start_date`, `end_date`: Date range filtering

### Committees API
```
GET /committees
```
- **Description**: Get committee information
- **Parameters**:
  - `apikey`: Required API key
  - `jurisdiction`: Filter by state
  - `organization`: Filter by parent organization

## SQL Data Model

### Core Tables (migrations/003_openstates_schema_optimized.sql)

#### Reference Tables
```sql
-- Jurisdictions (states, counties, municipalities)
CREATE TABLE openstates.jurisdictions (
    jurisdiction_id       text PRIMARY KEY, -- ocd-jurisdiction format
    name                 text NOT NULL,
    classification       text NOT NULL, -- state, municipality
    state_code           text NOT NULL, -- Two-letter state code
    url                  text,
    latest_bill_update   timestamptz,
    latest_people_update  timestamptz,
    -- Full-text search vector
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Legislative sessions
CREATE TABLE openstates.legislative_sessions (
    session_id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id       text NOT NULL REFERENCES openstates.jurisdictions(jurisdiction_id),
    identifier            text NOT NULL,
    name                 text NOT NULL,
    classification       text NOT NULL,
    start_date           date,
    end_date             date,
    is_active            boolean DEFAULT false,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (jurisdiction_id, identifier)
);
```

#### Organizations (Committees, Legislatures)
```sql
CREATE TABLE openstates.organizations (
    organization_id       text PRIMARY KEY, -- ocd-organization format
    name                 text NOT NULL,
    classification       text NOT NULL, -- legislature, executive, committee
    jurisdiction_id       text REFERENCES openstates.jurisdictions(jurisdiction_id),
    parent_id            text REFERENCES openstates.organizations(organization_id),
    -- Full-text search vector
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### People/Legislators
```sql
CREATE TABLE openstates.people (
    person_id            text PRIMARY KEY, -- ocd-person format
    name                 text NOT NULL,
    family_name          text NOT NULL,
    given_name           text NOT NULL,
    image                text,
    gender               text,
    biography            text,
    birth_date           date,
    death_date           date,
    primary_party        text,
    jurisdiction_id       text REFERENCES openstates.jurisdictions(jurisdiction_id),
    current_role_data     jsonb, -- Current role information as JSON
    -- Full-text search vector
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(biography, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Bills
```sql
CREATE TABLE openstates.bills (
    bill_id              text PRIMARY KEY, -- ocd-bill format
    identifier           text NOT NULL, -- e.g., "AB 123" or "SB 456"
    title                text NOT NULL,
    classification       text[] NOT NULL, -- bill type classifications
    subject              text[] NOT NULL, -- subject areas
    jurisdiction_id       text REFERENCES openstates.jurisdictions(jurisdiction_id),
    session_id           uuid REFERENCES openstates.legislative_sessions(session_id),
    from_organization_id text REFERENCES openstates.organizations(organization_id),
    first_action_date    date,
    latest_action_date   date,
    latest_action_desc   text,
    -- Full-text search vector
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(latest_action_desc, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Bill Actions
```sql
CREATE TABLE openstates.bill_actions (
    action_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              text NOT NULL REFERENCES openstates.bills(bill_id) ON DELETE CASCADE,
    description          text NOT NULL,
    date                 date NOT NULL,
    classification       text[] NOT NULL, -- action type classifications
    order_sequence       integer NOT NULL,
    organization_id      text REFERENCES openstates.organizations(organization_id),
    -- Full-text search vector
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(description, '')), 'A')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Bill Sponsorships
```sql
CREATE TABLE openstates.bill_sponsorships (
    sponsorship_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id              text NOT NULL REFERENCES openstates.bills(bill_id) ON DELETE CASCADE,
    person_id            text REFERENCES openstates.people(person_id),
    organization_id      text REFERENCES openstates.organizations(organization_id),
    name                 text NOT NULL, -- Sponsor name if not linked to person
    is_primary           boolean NOT NULL DEFAULT false,
    classification       text NOT NULL, -- sponsor type
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Voting System
```sql
CREATE TABLE openstates.vote_events (
    vote_id              text PRIMARY KEY, -- ocd-vote format
    identifier           text NOT NULL, -- Vote identifier
    motion_text          text NOT NULL,
    motion_classification text[] NOT NULL,
    start_date           timestamptz NOT NULL,
    result               text NOT NULL, -- pass, fail, etc.
    bill_id              text REFERENCES openstates.bills(bill_id),
    organization_id      text NOT NULL REFERENCES openstates.organizations(organization_id),
    -- Full-text search vector
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(motion_text, '')), 'A')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE openstates.person_votes (
    vote_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vote_event_id        text NOT NULL REFERENCES openstates.vote_events(vote_id) ON DELETE CASCADE,
    person_id            text REFERENCES openstates.people(person_id),
    option               text NOT NULL, -- yes, no, abstain, etc.
    voter_name           text NOT NULL, -- Name if person_id not available
    note                 text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (vote_event_id, person_id)
);
```

#### Membership and Positions
```sql
CREATE TABLE openstates.memberships (
    membership_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id            text REFERENCES openstates.people(person_id),
    organization_id      text REFERENCES openstates.organizations(organization_id),
    label                text NOT NULL, -- Position label
    role                 text NOT NULL, -- Role title
    start_date           date,
    end_date             date,
    post_id              text, -- Associated position
    on_behalf_of_id      text REFERENCES openstates.organizations(organization_id),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE openstates.posts (
    post_id              text PRIMARY KEY, -- ocd-post format
    label                text NOT NULL,
    role                 text NOT NULL,
    jurisdiction_id       text REFERENCES openstates.jurisdictions(jurisdiction_id),
    organization_id      text REFERENCES openstates.organizations(organization_id),
    start_date           date,
    end_date             date,
    maximum_memberships  integer DEFAULT 1,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Events (Committee Hearings, etc.)
```sql
CREATE TABLE openstates.events (
    event_id             text PRIMARY KEY, -- ocd-event format
    name                 text NOT NULL,
    description          text NOT NULL,
    classification       text NOT NULL,
    start_date           timestamptz,
    end_date             timestamptz,
    all_day              boolean DEFAULT false,
    timezone             text,
    status               text NOT NULL,
    jurisdiction_id       text NOT NULL REFERENCES openstates.jurisdictions(jurisdiction_id),
    -- Full-text search vector
    search_document      tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B')
    ) STORED,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
```

#### Performance Indexes
```sql
-- Optimized indexes for state-level data
CREATE INDEX IF NOT EXISTS idx_openstates_jurisdictions_state ON openstates.jurisdictions(state_code);
CREATE INDEX IF NOT EXISTS idx_openstates_jurisdictions_search ON openstates.jurisdictions USING GIN (search_document);

CREATE INDEX IF NOT EXISTS idx_openstates_people_jurisdiction ON openstates.people(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_openstates_people_party ON openstates.people(primary_party);
CREATE INDEX IF NOT EXISTS idx_openstates_people_search ON openstates.people USING GIN (search_document);

CREATE INDEX IF NOT EXISTS idx_openstates_bills_jurisdiction ON openstates.bills(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_openstates_bills_session ON openstates.bills(session_id);
CREATE INDEX IF NOT EXISTS idx_openstates_bills_dates ON openstates.bills(latest_action_date, first_action_date);
CREATE INDEX IF NOT EXISTS idx_openstates_bills_search ON openstates.bills USING GIN (search_document);
CREATE INDEX IF NOT EXISTS idx_openstates_bills_subjects ON openstates.bills USING GIN (classification);

CREATE INDEX IF NOT EXISTS idx_openstates_bill_actions_bill ON openstates.bill_actions(bill_id, order_sequence);
CREATE INDEX IF NOT EXISTS idx_openstates_bill_actions_date ON openstates.bill_actions(date);
CREATE INDEX IF NOT EXISTS idx_openstates_bill_actions_search ON openstates.bill_actions USING GIN (search_document);

CREATE INDEX IF NOT EXISTS idx_openstates_sponsorships_bill ON openstates.bill_sponsorships(bill_id);
CREATE INDEX IF NOT EXISTS idx_openstates_sponsorships_person ON openstates.bill_sponsorships(person_id);

CREATE INDEX IF NOT EXISTS idx_openstates_vote_events_bill ON openstates.vote_events(bill_id);
CREATE INDEX IF NOT EXISTS idx_openstates_vote_events_org ON openstates.vote_events(organization_id);
CREATE INDEX IF NOT EXISTS idx_openstates_vote_events_date ON openstates.vote_events(start_date);
CREATE INDEX IF NOT EXISTS idx_openstates_vote_events_search ON openstates.vote_events USING GIN (search_document);

CREATE INDEX IF NOT EXISTS idx_openstates_person_votes_vote ON openstates.person_votes(vote_event_id);
CREATE INDEX IF NOT EXISTS idx_openstates_person_votes_person ON openstates.person_votes(person_id);

CREATE INDEX IF NOT EXISTS idx_openstates_memberships_person ON openstates.memberships(person_id);
CREATE INDEX IF NOT EXISTS idx_openstates_memberships_org ON openstates.memberships(organization_id);
CREATE INDEX IF NOT EXISTS idx_openstates_memberships_dates ON openstates.memberships(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_openstates_events_jurisdiction ON openstates.events(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_openstates_events_dates ON openstates.events(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_openstates_events_search ON openstates.events USING GIN (search_document);
```

## SQL Functions and Procedures

### Incremental Ingestion Functions
```sql
-- Checkpoint management for jurisdictions
SELECT incremental.get_or_create_checkpoint('openstates.org', 'people', 'ca', NULL);
SELECT incremental.update_checkpoint_progress(
    'openstates.org', 'people', 'ca',
    NULL, last_page, NULL, NULL,
    records_processed, is_completed
);

-- Duplicate detection for state-level data
SELECT incremental.is_record_processed(
    'openstates.org', 'people', person_id, person_data::jsonb
);

-- Session management
CALL incremental.start_ingestion_session(
    'openstates_people_ca_20250101_120000',
    'openstates.org',
    'people',
    '{"jurisdiction": "ca", "batch_size": 50}'
);
CALL incremental.complete_ingestion_session(session_id, 'completed', NULL);

-- Get next ingestion parameters
SELECT * FROM incremental.get_next_ingestion_params(
    'openstates.org', 'people', 'ca'
);
```

## Python Ingestion Functions

### Primary Class: IncrementalOpenStatesIngestor

#### Core Methods
```python
class IncrementalOpenStatesIngestor:
    def __init__(self):
        # Initialize API key validation
        # Setup base URL, batch size, database connection
        # Validate OPENSTATES_API_KEY environment variable
        # Enable OpenStates-specific configuration

    def get_next_ingestion_params(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Get next ingestion parameters for jurisdiction-specific resuming"""

    def create_checkpoint(self, jurisdiction: str = None, total_estimated: int = None):
        """Create or get checkpoint for this jurisdiction"""

    def update_checkpoint(self, jurisdiction: str = None, last_page: int = None,
                         records_processed: int = 0, is_completed: bool = False):
        """Update checkpoint progress with page-based pagination"""

    def is_record_processed(self, person_id: str, person_data: Dict[str, Any]) -> bool:
        """Check if record already processed using SHA-256 fingerprinting"""
```

#### API Client Methods
```python
    def fetch_people_batch(self, jurisdiction: str = None, page: int = 1) -> Dict[str, Any]:
        """Fetch a batch of people from OpenStates API"""
        # Uses adaptive rate limiting
        # Supports jurisdiction filtering
        # Handles API pagination with max 50 per page
        # Returns structured results with pagination metadata
        # Applies exponential backoff for rate limits

    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string in various formats"""
        # Handles multiple date formats (ISO, US, etc.)
        # Graceful handling of invalid dates
        # Returns standardized YYYY-MM-DD format
```

#### Data Processing Methods
```python
    def normalize_person_data(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform API person data to database format"""
        # Extract OCD-compliant person ID
        # Parse jurisdiction information
        # Handle current role data as JSONB
        # Normalize name components (given_name, family_name)
        # Map party affiliation and biographical data

    def insert_people_batch(self, people: List[Dict[str, Any]]) -> int:
        """Insert batch of people with UPSERT conflict handling"""
        # Use psycopg2.extras.execute_values for bulk insertion
        # Handle person_id conflicts with ON CONFLICT
        # Support JSONB current_role_data storage
        # Return count of successfully inserted records
```

#### Session Management Methods
```python
    def start_ingestion_session(self, jurisdiction: str = None) -> str:
        """Start jurisdiction-specific ingestion session"""
        # Generate unique session ID with jurisdiction
        # Log session start with jurisdiction metadata
        # Record batch size and jurisdiction info

    def complete_ingestion_session(self, session_id: str, status: str = 'completed', error_summary: str = None):
        """Complete ingestion session with jurisdiction summary"""
        # Update session with final status
        # Record jurisdiction-specific statistics
        # Log any errors or processing summaries
```

#### Main Ingestion Methods
```python
    def ingest_people(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Main method to ingest people for specific jurisdiction"""
        # Check existing checkpoint for jurisdiction progress
        # Create checkpoint if needed
        # Start tracking session with jurisdiction metadata
        # Process paginated people data
        # Handle deduplication via fingerprinting
        # Update progress after each page
        # Mark completion and finalize session

    def ingest_all_jurisdictions(self, jurisdictions: List[str] = None):
        """Ingest people across multiple jurisdictions"""
        # Default to major US states if no list provided
        # Loop through jurisdiction list
        # Handle individual jurisdiction failures
        # Provide comprehensive summary statistics
        # Return detailed results for each jurisdiction
```

### Key Ingestion Flow
1. **API Key Validation**: Verify `OPENSTATES_API_KEY` environment variable
2. **Jurisdiction Selection**: Choose specific states or all available
3. **Checkpoint Resume**: Continue from last processed page per jurisdiction
4. **Paginated Fetch**: Get people data in batches (max 50 per page)
5. **Data Normalization**: Transform to OCD-compliant format and database schema
6. **Duplicate Detection**: Use SHA-256 fingerprinting to avoid reprocessing
7. **Bulk Insertion**: UPSERT people with OCD identifier conflicts
8. **Progress Tracking**: Update checkpoints after each page
9. **Session Completion**: Log jurisdiction-specific final status

### Rate Limiting and Error Handling
- **Adaptive Rate Limiting**: Monitor OpenStates API response headers
- **Exponential Backoff**: Handle 429 rate limit errors with progressive delays
- **Retry Logic**: 3 attempts with increasing backoff intervals
- **Database Transactions**: Automatic rollback on failures
- **Comprehensive Logging**: Track all operations, errors, and jurisdiction progress
- **Error Isolation**: Individual jurisdiction failures don't stop overall process

### Performance Characteristics
- **Batch Size**: Configurable (default: 50 people per batch, API max: 50)
- **Pagination**: Page-based with automatic detection of max page
- **Processing Speed**: ~50 records per page with full validation
- **API Response Time**: <2 seconds average response time
- **Database Operations**: Optimized batch UPSERT operations with JSONB support
- **Memory Usage**: Streaming processing to handle large jurisdiction datasets
- **Resume Capability**: Page-based checkpoint recovery for interrupted processes

### OpenStates-Specific Features
- **OCD Compliance**: All identifiers follow Open Civic Data standards
- **Multi-State Support**: Simultaneous ingestion across multiple states
- **Jurisdiction Filtering**: Efficient filtering by state/county/municipality
- **Role Management**: Comprehensive handling of current and historical roles
- **Committee Integration**: Full support for committee structures and memberships
- **Event Tracking**: Support for hearings, meetings, and other legislative events
- **Rich Metadata**: JSONB storage for flexible, schema-evolving data structures
