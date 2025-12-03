# Congress CLI Functions Documentation

This document provides a comprehensive summary of all functions in the `congress_cli.py` tool, which is designed for ingesting Congress.gov data into a PostgreSQL database.

## Overview

The `CongressCLI` class provides a complete pipeline for extracting, transforming, and loading (ETL) Congress data from the Congress.gov API into a normalized PostgreSQL database schema.

## Core Class: CongressCLI

### Initialization & Utility Methods

#### `__init__(api_key, db_config, batch_size=50, dry_run=False)`
Constructor that initializes the CLI with:
- **api_key**: Congress.gov API key
- **db_config**: PostgreSQL database configuration
- **batch_size**: Number of records to process per batch (default: 50)
- **dry_run**: If True, simulates operations without making database changes

#### `connect_db()`
Establishes PostgreSQL database connection using provided configuration.

#### `close_db()`
Properly closes the database connection.

#### `get(endpoint, params=None)`
Makes authenticated GET requests to the Congress.gov API with:
- Error handling for failed requests
- Rate limiting compliance
- JSON response parsing

## Data Transformation Functions

These functions transform raw API data into database-ready tuples for batch insertion:

### `transform_member(member_data, congress)`
Transforms Congress member data:
- **Input**: Member API response with bioguideId, fullName, party, state, district
- **Output**: Tuple with (bioguide_id, full_name, first_name, last_name, party, state, district, congress_number, active, created_at)

### `transform_bill(bill_data, congress)`
Transforms bill data:
- **Input**: Bill API response with type, number, originChamber, introducedDate
- **Output**: Tuple with (congress_number, bill_type, bill_number, origin_chamber, introduced_date, latest_action_date, latest_action_text, policy_area, official_title, sponsor_bioguide_id, created_at)
- **Features**: Chamber code mapping (House→house, Senate→senate, Joint→joint)

### `transform_amendment(amendment_data, congress)`
Transforms amendment data:
- **Input**: Amendment API response
- **Output**: Tuple with (congress_number, amendment_type, amendment_number, description, purpose, latest_action_date, latest_action_text, submitted_date, created_at)

### `transform_session(session_data)`
Transforms congressional session data:
- **Output**: Tuple with (congress, session_number, type, start_date, end_date, created_at)

### `transform_chamber(chamber_data)`
Transforms chamber information:
- **Output**: Tuple with (chamber_code, name, type, created_at)

### `transform_congress_committee(committee_data)`
Transforms committee data:
- **Output**: Tuple with (committee_code, name, chamber, parent_committee_code, type, jurisdiction, created_at)

### `transform_vote(vote_data)`
Transforms vote data:
- **Output**: Tuple with (congress, session, roll_call_number, question, result, date, positions_json, created_at)

### `transform_document_metadata(doc_data)`
Transforms document metadata:
- **Output**: Tuple with (document_hash, title, description, content_type, retrieved_at, created_at)

## Data Ingestion Functions

These functions handle the complete ingestion pipeline for different data types:

### `ingest_members(congress)`
Ingests Congress members:
- **Process**: Pagination with batch processing
- **API Endpoint**: `/member/congress/{congress}`
- **Database**: `congress.members` table
- **Key**: bioguide_id (with upsert logic)
- **Features**:
  - Filters members without bioguideId
  - Progress tracking
  - Rate limiting (0.1s delays)

### `ingest_bills(congress)`
Ingests all bills for a congress:
- **Process**: Iterates through all bills with pagination
- **API Endpoint**: `/bill?congress={congress}`
- **Database**: `congress.bills` table
- **Key**: (congress_number, bill_type, bill_number)
- **Features**: Only processes bills with valid numbers

### `ingest_amendments(congress)`
Ingests amendments:
- **Process**: Batch processing with automatic table creation
- **API Endpoint**: `/amendment?congress={congress}`
- **Database**: `congress.amendments` table
- **Key**: (congress_number, amendment_type, amendment_number)
- **Features**: Creates table if it doesn't exist

### `ingest_summaries(congress)`
Ingests bill summaries:
- **Process**: Two-level iteration (bills → summaries)
- **API Endpoints**:
  - `/bill?congress={congress}` (list bills)
  - `/bill/{congress}/{type}/{number}/summaries` (fetch summaries)
- **Database**: `congress.bill_summaries` table
- **Key**: (congress_number, bill_type, bill_number, action_date)
- **Features**: Supports multiple summaries per bill

### `ingest_text(congress)`
Ingests bill text versions:
- **Process**: Two-level iteration (bills → text versions)
- **API Endpoints**:
  - `/bill?congress={congress}` (list bills)
  - `/bill/{congress}/{type}/{number}/text` (fetch text versions)
- **Database**: `congress.bill_text_versions` table
- **Key**: (congress_number, bill_type, bill_number, version_code, format)
- **Features**: Stores multiple formats per version

### `status()`
Shows current data status:
- **Tables Checked**: members, bills, amendments, bill_summaries, bill_text_versions
- **Output**: Record counts or "Not initialized" for missing tables
- **Features**: Handles missing tables gracefully

## Main CLI Interface

### `main()`
Command-line entry point:
- **Arguments**:
  - `--dry-run`: Run without making changes
  - `--batch-size`: Override default batch size (50)
- **Subcommands**:
  - `ingest-members <congress>`: Ingest members
  - `ingest-bills <congress>`: Ingest bills
  - `ingest-amendments <congress>`: Ingest amendments
  - `ingest-summaries <congress>`: Ingest summaries
  - `ingest-text <congress>`: Ingest text versions
  - `status`: Show data status
- **Configuration**:
  - Requires `CONGRESS_API_KEY` environment variable
  - Database connection to 'opendiscourse' database
  - User: 'cbwinslow'
  - Socket: '/var/run/postgresql'

## Key Features

### Performance & Reliability
- **Batch Processing**: Configurable batch sizes for efficient database operations
- **Rate Limiting**: 0.1-second delays between API calls to respect rate limits
- **Error Handling**: Comprehensive error handling with database rollback capabilities
- **Progress Tracking**: Real-time progress reporting during ingestion

### Data Integrity
- **Upsert Logic**: Uses PostgreSQL `ON CONFLICT` clauses for data consistency
- **Dry Run Mode**: Safe testing without making database changes
- **Data Validation**: Filters invalid or incomplete records before insertion

### Database Management
- **Automatic Table Creation**: Creates tables automatically if they don't exist
- **Connection Management**: Proper connection lifecycle management
- **Transaction Safety**: Uses transactions with rollback on failures

## Usage Examples

```bash
# Ingest members for 118th Congress
python scripts/ingestion/congress_cli.py ingest-members 118

# Ingest bills with custom batch size
python scripts/ingestion/congress_cli.py --batch-size 100 ingest-bills 118

# Dry run for testing
python scripts/ingestion/congress_cli.py --dry-run ingest-summaries 118

# Check data status
python scripts/ingestion/congress_cli.py status
```

## Error Handling

All ingestion functions include:
- Database connection validation
- API request error handling
- Batch operation error handling with rollback
- Progress reporting even on failures
- Graceful termination on unrecoverable errors

## Database Schema

The tool expects the following PostgreSQL schema:
- `congress.members`: Member information
- `congress.bills`: Bill details
- `congress.amendments`: Amendment data
- `congress.bill_summaries`: Bill summaries with action tracking
- `congress.bill_text_versions`: Text versions and formats

Each table includes `created_at` and `updated_at` timestamp columns for audit trails.
