# OpenStates API Data Ingestion Workflow

This guide provides step-by-step instructions for ingesting state-level legislative data from the OpenStates API (api.openstates.org) into your SQL database.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Step 1: API Key Setup](#step-1-api-key-setup)
- [Step 2: Database Setup](#step-2-database-setup)
- [Step 3: Data Ingestion](#step-3-data-ingestion)
- [Step 4: Verification](#step-4-verification)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Prerequisites

Before starting, ensure you have:
- Python 3.13+ installed
- PostgreSQL 14+ with pgvector extension
- Access to your PostgreSQL database
- Internet connection for API access

## Step 1: API Key Setup

### 1.1 Obtain API Key

1. Visit the OpenStates API page: https://openstates.org/api/
2. Click "Sign up for an API key"
3. Create an account or sign in with your existing account
4. Your API key will be available in your account dashboard
5. Note: OpenStates offers a free tier with generous rate limits

### 1.2 Configure API Key

Set your API key as an environment variable:

```bash
# Linux/macOS
export OPENSTATES_API_KEY="your_api_key_here"

# Windows (Command Prompt)
set OPENSTATES_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:OPENSTATES_API_KEY="your_api_key_here"
```

Or add it to your `.env` file in the project root:

```bash
echo "OPENSTATES_API_KEY=your_api_key_here" >> .env
```

## Step 2: Database Setup

### 2.1 Database Schema Notes

OpenStates data uses the same GovInfo schema with some adaptations:
- State legislators map to `govinfo.members` table
- State bills use `govinfo.bills` table with state-specific metadata
- State committees use `govinfo.committees` table
- Vote records use `govinfo.votes` table

### 2.2 Run SQL Migrations

If you haven't already set up the database for Congress/GovInfo data:

```bash
# Navigate to the project root
cd /path/to/opendiscourse

# Run the table creation script
psql -h localhost -U postgres -d opendiscourse -f govinfo/sql/001_create_tables.sql

# Run the indexes script
psql -h localhost -U postgres -d opendiscourse -f govinfo/sql/002_indexes.sql
```

### 2.3 Verify Database Schema

Check that the tables exist:

```sql
-- Connect to your database
psql -h localhost -U postgres -d opendiscourse

-- List tables in the govinfo schema
\dt govinfo.*

-- Key tables for OpenStates data:
-- govinfo.members (legislators)
-- govinfo.bills (state bills)
-- govinfo.votes (state votes)
-- govinfo.committees (state committees)
-- govinfo.memberships (committee memberships)
```

## Step 3: Data Ingestion

### 3.1 Available Ingestion Methods

The repository provides functions for OpenStates ingestion in the following locations:

1. **opendiscourse/ingestion/membership_ingestion.py** - For legislator data
2. **scripts/data_ingestion/source_ingestion_tasks.py** - For bill data
3. **scripts/data_ingestion/crawl4ai_openrouter.py** - For automated crawling

### 3.2 Method 1: Ingesting Legislator Data

Use the built-in function to fetch and ingest legislator information:

```python
# Create a Python script: ingest_openstates_legislators.py

import os
from opendiscourse.ingestion.membership_ingestion import (
    fetch_openstates_legislators,
    ingest_membership_data
)

# Configuration
STATE = "ny"  # New York state
SESSION = "2023-2024"
API_KEY = os.getenv("OPENSTATES_API_KEY")

# Fetch legislators
legislators = fetch_openstates_legislators(STATE, SESSION, API_KEY)

if legislators:
    print(f"Fetched {len(legislators)} legislators")
    
    # Process each legislator
    for legislator in legislators:
        # Transform to membership data format
        membership_data = {
            "membership_id": legislator.get("id"),
            "member_id": legislator.get("id"),
            "full_name": legislator.get("name"),
            "party_code": legislator.get("party"),
            "state": STATE,
            "chamber_code": legislator.get("chamber"),
            "district": legislator.get("district"),
            # Add more fields as needed
        }
        
        # Ingest to database
        result = ingest_membership_data(membership_data)
        if result:
            print(f"Successfully ingested: {legislator.get('name')}")
        else:
            print(f"Failed to ingest: {legislator.get('name')}")
else:
    print("Failed to fetch legislators")
```

Run the script:

```bash
python ingest_openstates_legislators.py
```

### 3.3 Method 2: Ingesting Bill Data

Create a custom script using OpenStates API v3:

```python
# Create a Python script: ingest_openstates_bills.py

import os
import requests
import psycopg2
from datetime import datetime

API_KEY = os.getenv("OPENSTATES_API_KEY")
BASE_URL = "https://v3.openstates.org/graphql"

def fetch_state_bills(state, session, limit=100):
    """Fetch bills using GraphQL API."""
    
    query = """
    query($jurisdiction: String!, $session: String!, $first: Int!) {
      bills(
        jurisdiction: $jurisdiction
        session: $session
        first: $first
      ) {
        edges {
          node {
            id
            identifier
            title
            classification
            subject
            updatedAt
            createdAt
            firstActionDate
            latestActionDate
            latestActionDescription
            sponsorships {
              name
              primary
              classification
            }
            actions {
              description
              date
              classification
            }
            votes {
              identifier
              motionText
              result
              startDate
            }
          }
        }
      }
    }
    """
    
    variables = {
        "jurisdiction": state,
        "session": session,
        "first": limit
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        BASE_URL,
        json={"query": query, "variables": variables},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {}).get("bills", {}).get("edges", [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

def ingest_bills_to_database(bills, state):
    """Insert bills into PostgreSQL database."""
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "opendiscourse"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )
    
    cursor = conn.cursor()
    
    for edge in bills:
        bill = edge["node"]
        
        # Insert bill
        insert_query = """
        INSERT INTO govinfo.bills (
            bill_id, bill_type, bill_number, chamber_code,
            introduced_date, latest_action_date, latest_action_text,
            status, subjects_primary, sponsors, summaries,
            last_updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (bill_id) 
        DO UPDATE SET
            latest_action_date = EXCLUDED.latest_action_date,
            latest_action_text = EXCLUDED.latest_action_text,
            last_updated_at = EXCLUDED.last_updated_at
        """
        
        cursor.execute(insert_query, (
            f"{state}-{bill['identifier']}",
            bill.get("classification", ["bill"])[0],
            bill["identifier"],
            state,
            bill.get("firstActionDate"),
            bill.get("latestActionDate"),
            bill.get("latestActionDescription"),
            "active",
            ", ".join(bill.get("subject", [])),
            str(bill.get("sponsorships", [])),
            str({"title": bill.get("title")}),
            datetime.now()
        ))
        
        print(f"Ingested bill: {bill['identifier']} - {bill.get('title', 'No title')[:50]}...")
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Successfully ingested {len(bills)} bills")

# Main execution
if __name__ == "__main__":
    STATE = "ny"  # Change to your desired state
    SESSION = "2023-2024"  # Change to desired session
    
    print(f"Fetching bills for {STATE}, session {SESSION}...")
    bills = fetch_state_bills(STATE, SESSION, limit=100)
    
    if bills:
        print(f"Fetched {len(bills)} bills")
        ingest_bills_to_database(bills, STATE)
    else:
        print("No bills fetched")
```

Run the script:

```bash
python ingest_openstates_bills.py
```

### 3.4 Method 3: Using Existing Crawl Pipeline

The repository includes integration with the crawl pipeline:

```bash
# Navigate to scripts directory
cd scripts/data_ingestion

# Review the configuration in crawl4ai_openrouter.py
# Look for the openstates_recent source definition

# Run the crawl pipeline (requires additional setup)
python run_crawl_pipeline.py
```

### 3.5 State Codes

OpenStates uses two-letter state abbreviations (lowercase):

Common states:
- `al` - Alabama
- `ak` - Alaska
- `az` - Arizona
- `ca` - California
- `fl` - Florida
- `ny` - New York
- `tx` - Texas
- `wa` - Washington
- (and all other US states and territories)

### 3.6 Understanding the Ingestion Process

The OpenStates ingestion process:

1. **Fetches legislator data** via REST or GraphQL API
2. **Downloads bill information** including:
   - Bill identifiers and titles
   - Sponsors and cosponsors
   - Bill actions and timeline
   - Vote records
   - Committee assignments
3. **Transforms data** to match the database schema
4. **Stores data** in PostgreSQL tables:
   - `govinfo.members` - Legislator information
   - `govinfo.bills` - Bill details
   - `govinfo.bill_actions` - Legislative actions
   - `govinfo.votes` - Vote records
   - `govinfo.committees` - Committee information
   - `govinfo.memberships` - Committee memberships

## Step 4: Verification

### 4.1 Verify Legislator Data

Query the database to verify legislator data was ingested:

```sql
-- Count legislators by state
SELECT state, COUNT(*) as legislator_count
FROM govinfo.members
WHERE state IS NOT NULL
GROUP BY state
ORDER BY legislator_count DESC;

-- View legislators from a specific state
SELECT member_id, full_name, party_code, state, district
FROM govinfo.members
WHERE state = 'ny'
ORDER BY full_name
LIMIT 10;

-- Check committee memberships
SELECT m.full_name, c.committee_name, ms.role
FROM govinfo.members m
JOIN govinfo.memberships ms ON m.member_id = ms.member_id
JOIN govinfo.committees c ON ms.committee_code = c.committee_code
WHERE m.state = 'ny'
LIMIT 10;
```

### 4.2 Verify Bill Data

Query the database to verify bill data was ingested:

```sql
-- Count bills by state (check bill_id prefix)
SELECT 
    SUBSTRING(bill_id FROM 1 FOR 2) as state,
    COUNT(*) as bill_count
FROM govinfo.bills
WHERE LENGTH(bill_id) > 2
GROUP BY SUBSTRING(bill_id FROM 1 FOR 2)
ORDER BY bill_count DESC;

-- View recent state bills
SELECT bill_id, bill_number, chamber_code, latest_action_date
FROM govinfo.bills
WHERE bill_id LIKE 'ny-%'  -- Change 'ny' to your state
ORDER BY latest_action_date DESC
LIMIT 10;

-- Check bill actions
SELECT b.bill_number, ba.action_date, ba.action_text
FROM govinfo.bills b
JOIN govinfo.bill_actions ba ON b.bill_id = ba.bill_id
WHERE b.bill_id LIKE 'ny-%'
ORDER BY ba.action_date DESC
LIMIT 10;
```

### 4.3 Verify Vote Records

Query the database to verify vote data:

```sql
-- Count votes by state
SELECT chamber_code, COUNT(*) as vote_count
FROM govinfo.votes
WHERE chamber_code IN (
    SELECT DISTINCT state FROM govinfo.members WHERE state IS NOT NULL
)
GROUP BY chamber_code
ORDER BY vote_count DESC;

-- View recent votes
SELECT vote_id, vote_question, vote_result, vote_date
FROM govinfo.votes
ORDER BY vote_date DESC
LIMIT 10;
```

### 4.4 Review Logs

Check for any errors during ingestion:

```bash
# Search for OpenStates-related errors
grep -i "openstates" data/logs/ingestion.log

# Check for API errors
grep "Error" data/logs/ingestion.log | tail -20
```

## Troubleshooting

### Issue: API Key Not Found

**Error:** `Missing API key`

**Solution:** Ensure your API key is properly set:

```bash
echo $OPENSTATES_API_KEY  # Should display your key
```

### Issue: Rate Limiting

**Error:** `429 Too Many Requests`

**Solution:** 
- OpenStates free tier: 100 requests per minute, 10,000 per month
- Add delays between requests
- Consider upgrading to a paid tier for higher limits
- Implement exponential backoff in your script

### Issue: Invalid State Code

**Error:** `Invalid jurisdiction`

**Solution:** 
- Use lowercase two-letter state codes (e.g., 'ny', not 'NY' or 'New York')
- Verify the state code at: https://docs.openstates.org/en/latest/api/v3/

### Issue: GraphQL Query Error

**Error:** `GraphQL query failed`

**Solution:**
1. Verify your query syntax using the GraphQL explorer: https://v3.openstates.org/graphql
2. Check that all field names are correct
3. Ensure API key is included in headers

### Issue: Database Foreign Key Constraint

**Error:** `Foreign key constraint violation`

**Solution:**
- Ensure you ingest legislators before their related data (bills, votes)
- Use `ON CONFLICT` clauses to handle duplicates
- Check that referenced IDs exist in parent tables

### Issue: Session Not Found

**Error:** `No data for session`

**Solution:**
- Verify the session format (usually "YYYY-YYYY" or "YYYY")
- Check available sessions for your state: `https://v3.openstates.org/jurisdictions/{state}`
- Some states use different session naming conventions

## API Reference

### OpenStates API v3

The current version of the OpenStates API is v3, which uses GraphQL.

**Base URL:** `https://v3.openstates.org/graphql`

**Authentication:** Include your API key in the `X-API-Key` header

### Common GraphQL Queries

#### Fetch Legislators:

```graphql
query($jurisdiction: String!, $session: String!) {
  people(
    memberOf: $jurisdiction
    everMemberOf: $session
  ) {
    edges {
      node {
        id
        name
        currentMemberships {
          organization {
            name
            classification
          }
          post {
            label
          }
        }
        contactDetails {
          type
          value
        }
      }
    }
  }
}
```

#### Fetch Bills:

```graphql
query($jurisdiction: String!, $session: String!) {
  bills(
    jurisdiction: $jurisdiction
    session: $session
  ) {
    edges {
      node {
        id
        identifier
        title
        subject
        sponsorships {
          name
          primary
        }
        actions {
          description
          date
        }
      }
    }
  }
}
```

#### Fetch Votes:

```graphql
query($billId: String!) {
  bill(id: $billId) {
    votes {
      identifier
      motionText
      result
      startDate
      counts {
        option
        value
      }
      votes {
        voterName
        option
      }
    }
  }
}
```

### Rate Limits

- **Free Tier:** 100 requests per minute, 10,000 requests per month
- **Plus Tier:** 500 requests per minute, 100,000 requests per month
- **Pro Tier:** 1,000 requests per minute, unlimited requests

### Pagination

OpenStates uses cursor-based pagination:

```graphql
query($jurisdiction: String!, $after: String) {
  bills(
    jurisdiction: $jurisdiction
    first: 100
    after: $after
  ) {
    edges {
      node { id }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Advanced Usage

### Automated Scheduled Ingestion

Set up a cron job for regular updates:

```bash
# Edit crontab
crontab -e

# Add daily ingestion at 4 AM
0 4 * * * cd /path/to/opendiscourse && /path/to/venv/bin/python ingest_openstates_bills.py >> /var/log/openstates_ingest.log 2>&1
```

### Multi-State Ingestion

Create a script to ingest data from multiple states:

```python
# ingest_multiple_states.py

STATES = ['ny', 'ca', 'tx', 'fl', 'wa']
SESSION = '2023-2024'

for state in STATES:
    print(f"\nProcessing {state}...")
    
    # Fetch and ingest legislators
    legislators = fetch_openstates_legislators(state, SESSION, API_KEY)
    if legislators:
        for legislator in legislators:
            # Process legislator...
            pass
    
    # Fetch and ingest bills
    bills = fetch_state_bills(state, SESSION, limit=500)
    if bills:
        ingest_bills_to_database(bills, state)
    
    # Add delay to respect rate limits
    time.sleep(2)

print("\nAll states processed!")
```

### Incremental Updates

Track the last update time to fetch only new/updated data:

```python
import json
from datetime import datetime

# Load last update time
try:
    with open('last_update.json', 'r') as f:
        last_update = json.load(f)
except FileNotFoundError:
    last_update = {}

# Fetch bills updated since last run
last_timestamp = last_update.get('ny', '2024-01-01T00:00:00')

query = """
query($jurisdiction: String!, $updatedSince: DateTime!) {
  bills(
    jurisdiction: $jurisdiction
    updatedSince: $updatedSince
  ) {
    edges {
      node {
        id
        identifier
        updatedAt
      }
    }
  }
}
"""

# After ingestion, save current timestamp
last_update['ny'] = datetime.now().isoformat()
with open('last_update.json', 'w') as f:
    json.dump(last_update, f)
```

## Next Steps

After successfully ingesting OpenStates data:

1. **Review all three data sources** - See [DATA_INGESTION_MASTER.md](DATA_INGESTION_MASTER.md)
2. **Set up automated updates** - Configure cron jobs for regular data refresh
3. **Cross-reference data** - Link state and federal legislators
4. **Build state-level analytics** - Create dashboards for state legislative activity
5. **Compare across states** - Analyze legislative patterns across different states

## Support

For issues or questions:
- Check the [main workflow guide](DATA_INGESTION_MASTER.md)
- Review OpenStates documentation: https://docs.openstates.org/
- Visit OpenStates community: https://openstates.org/support/

## Resources

- OpenStates API v3 Documentation: https://docs.openstates.org/en/latest/api/v3/
- OpenStates GraphQL Explorer: https://v3.openstates.org/graphql
- OpenStates API Sign-up: https://openstates.org/api/
- OpenStates Data: https://openstates.org/data/
- State Legislature Finder: https://openstates.org/find_your_legislator/
