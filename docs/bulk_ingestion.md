# Bulk Data Ingestion CLIs

This directory contains CLI tools for ingesting data from OpenStates, Congress.gov, and GovInfo.gov. These tools are designed to be robust, handling rate limits and network errors automatically.

## Common Features
- **Rate Limiting**: Automatically respects API rate limits using a token bucket algorithm.
- **Retries**: Automatically retries failed requests with exponential backoff.
- **Dry Run**: Supports `--dry-run` flag to simulate ingestion without writing to the database.
- **Batch Processing**: Processes data in batches to optimize database inserts.

## OpenStates CLI (`scripts/ingestion/openstates_cli.py`)

Ingests state legislative data.

### Usage
```bash
# Ingest jurisdictions
python3 scripts/ingestion/openstates_cli.py ingest-jurisdictions

# Ingest people for a specific jurisdiction (e.g., California)
python3 scripts/ingestion/openstates_cli.py ingest-people state:ca

# Ingest bills
python3 scripts/ingestion/openstates_cli.py ingest-bills state:ca

# Ingest committees
python3 scripts/ingestion/openstates_cli.py ingest-committees state:ca

# Ingest events
python3 scripts/ingestion/openstates_cli.py ingest-events state:ca
```

## Congress CLI (`scripts/ingestion/congress_cli.py`)

Ingests federal legislative data from Congress.gov.

### Usage
```bash
# Ingest members for a specific congress (e.g., 118th)
python3 scripts/ingestion/congress_cli.py ingest-members 118

# Ingest bills
python3 scripts/ingestion/congress_cli.py ingest-bills 118

# Ingest amendments
python3 scripts/ingestion/congress_cli.py ingest-amendments 118

# Ingest sessions
python3 scripts/ingestion/congress_cli.py ingest-sessions

# Ingest chambers
python3 scripts/ingestion/congress_cli.py ingest-chambers
```

## GovInfo CLI (`scripts/ingestion/govinfo_cli.py`)

Ingests official government publications from GovInfo.gov.

### Usage
```bash
# Ingest collections metadata
python3 scripts/ingestion/govinfo_cli.py ingest-collections

# Ingest packages for a collection (e.g., BILLS)
python3 scripts/ingestion/govinfo_cli.py ingest-packages BILLS 2023-01-01 --end-date 2023-12-31

# Ingest granules for a specific package
python3 scripts/ingestion/govinfo_cli.py ingest-granules BILLS-118hr1ih
```

## Environment Variables

Ensure the following environment variables are set:
- `OPENSTATES_API_KEY`
- `CONGRESS_API_KEY`
- `GOVINFO_API_KEY`
- `DB_USER` (optional, defaults to `cbwinslow`)
- `DB_PASSWORD` (optional)
- `DB_HOST` (optional, defaults to unix socket)
