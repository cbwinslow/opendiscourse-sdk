# Bulk Data Ingestion - CLI Documentation

This document provides comprehensive usage instructions, examples, and endpoint coverage for the three main ingestion CLIs.

## Quick Start

All CLIs use environment variables for API keys (loaded via `scripts/utils/resource_manager.py`):
- `CONGRESS_API_KEY` or `CONGRESS_GOV_API_KEY`
- `OPENSTATES_API_KEY`
- `GOVINFO_API_KEY`

## Congress CLI (`congress_cli.py`)

### Features
- ✅ Rate limiting with exponential backoff
- ✅ Automatic pagination
- ✅ Dry-run mode for testing
- ✅ Resource manager integration

### Endpoint Coverage

#### Core Data
- **Members**: `ingest-members <congress>`
- **Bills**: `ingest-bills <congress> [--bill-type TYPE]`
- **Amendments**: `ingest-amendments <congress>`
- **Committees**: `ingest-committees <congress>`
- **Votes**: `ingest-votes <congress>` (House only)

#### Bill Details
- **Actions**: `ingest-bill-actions <congress>`
- **Cosponsors**: `ingest-bill-cosponsors <congress>`
- **Subjects**: `ingest-bill-subjects <congress>`
- **Titles**: `ingest-bill-titles <congress>`
- **Related Bills**: `ingest-related-bills <congress>`

#### Documents & Metadata
- **Summaries**: `ingest-summaries <congress>`
- **Text Versions**: `ingest-text <congress>`
- **Committee Reports**: `ingest-committee-reports <congress>`
- **Committee Prints**: `ingest-committee-prints <congress>`
- **Hearings**: `ingest-hearings <congress>`

#### Additional Data
- **Sessions**: `ingest-sessions`
- **Chambers**: `ingest-chambers`
- **Committee Members**: `ingest-committee-members <congress>`
- **Congressional Record**: `ingest-congressional-record`
- **Nominations**: `ingest-nominations <congress>`
- **Treaties**: `ingest-treaties <congress>`
- **House Communications**: `ingest-house-communications <congress>`
- **Senate Communications**: `ingest-senate-communications <congress>`

### Usage Examples

```bash
# Basic usage - current Congress (119)
python3 scripts/ingestion/congress_cli.py ingest-members 119

# Historical data - Congress 109-119 (2005-2025)
for congress in {109..119}; do
  python3 scripts/ingestion/congress_cli.py ingest-bills $congress
done

# Dry run to test
python3 scripts/ingestion/congress_cli.py --dry-run ingest-hearings 118

# Specific bill types
python3 scripts/ingestion/congress_cli.py ingest-bills 119 --bill-type hr

# Check status
python3 scripts/ingestion/congress_cli.py status
```

## OpenStates CLI (`openstates_cli.py`)

### Features
- ✅ Rate limiting with exponential backoff
- ✅ `--years-back` parameter for historical data
- ✅ Pagination support
- ✅ Resource manager integration
- ✅ Bulk ingestion for all states

### Endpoint Coverage

#### Core Data
- **Jurisdictions**: `ingest-jurisdictions`
- **People**: `ingest-people <jurisdiction>`
- **Bills**: `ingest-bills <jurisdiction> [--years-back N]`
- **Committees**: `ingest-committees <jurisdiction>`
- **Events**: `ingest-events <jurisdiction>`
- **Vote Events**: `ingest-vote-events <jurisdiction>`
- **Organizations**: `ingest-organizations <jurisdiction>`
- **Sessions**: `ingest-sessions <jurisdiction>`

#### Bulk Operations
- **All States**: `ingest-all-states`

### Usage Examples

```bash
# Jurisdictions (run first)
python3 scripts/ingestion/openstates_cli.py ingest-jurisdictions

# Single state - all data
python3 scripts/ingestion/openstates_cli.py ingest-people ca
python3 scripts/ingestion/openstates_cli.py ingest-bills ca

# Historical bills (20 years)
python3 scripts/ingestion/openstates_cli.py ingest-bills ca --years-back 20

# All states - comprehensive ingestion
python3 scripts/ingestion/openstates_cli.py ingest-all-states

# Check status
python3 scripts/ingestion/openstates_cli.py status
```

## GovInfo CLI (`govinfo_cli.py`)

### Features
- ✅ Rate limiting with exponential backoff
- ✅ Date range filtering
- ✅ Collection-based ingestion
- ✅ Resource manager integration

### Endpoint Coverage

#### Collections
- **List Collections**: `ingest-collections`
- **Collection Packages**: `ingest-collection <code> [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]`

#### Packages & Granules
- **Packages**: `ingest-packages <collection> <start_date> [--end-date DATE]`
- **Granules**: `ingest-granules <package_id>`

#### Committees
- **Committee Data**: `ingest-committees <start_date> [--end-date DATE]`

### Supported Collections
- `BILLS` - Congressional Bills
- `BILLSTATUS` - Bill Status
- `CRPT` - Committee Reports
- `CHRG` - Committee Hearings
- `FR` - Federal Register
- `PLAW` - Public Laws

### Usage Examples

```bash
# List available collections
python3 scripts/ingestion/govinfo_cli.py ingest-collections

# Ingest collection from 2005 to present
python3 scripts/ingestion/govinfo_cli.py ingest-collection BILLS --start-date 2005-01-01

# Specific date range
python3 scripts/ingestion/govinfo_cli.py ingest-packages FR 2020-01-01 --end-date 2020-12-31

# Committee hearings
python3 scripts/ingestion/govinfo_cli.py ingest-committees 2005-01-01

# Check status
python3 scripts/ingestion/govinfo_cli.py status
```

## 20-Year Bulk Ingestion Script

The `scripts/ingestion/run_20_year_ingestion.py` orchestrates parallel ingestion from all three sources.

### What It Does
- **Congress**: Ingests Congresses 109-119 (2005-2025)
  - Members, Bills (all types), Amendments, Committees, Votes
- **OpenStates**: 20 years for all 52 jurisdictions
  - People, Bills, Committees, Events, Vote Events
- **GovInfo**: Collections from 2005-present
  - BILLS, BILLSTATUS, CRPT, CHRG, FR, PLAW

### Usage

```bash
# Launch the massive ingestion (runs in background)
nohup python3 scripts/ingestion/run_20_year_ingestion.py > logs/20_year_ingestion_nohup.log 2>&1 &

# Monitor progress
tail -f logs/20_year_ingestion.log

# Check the report after completion
ls -lh ingestion_results/20_year_report_*.md
```

## Testing & Verification

### Dry Run Tests

```bash
# Test Congress CLI
python3 scripts/ingestion/congress_cli.py --dry-run ingest-bills 119

# Test OpenStates CLI
python3 scripts/ingestion/openstates_cli.py --dry-run ingest-bills ca --years-back 5

# Test GovInfo CLI
python3 scripts/ingestion/govinfo_cli.py --dry-run ingest-collection FR --start-date 2024-01-01
```

### Database Verification

```bash
# Check Congress data
python3 scripts/ingestion/congress_cli.py status

# Check OpenStates data
python3 scripts/ingestion/openstates_cli.py status

# Check GovInfo data
python3 scripts/ingestion/govinfo_cli.py status
```

### Manual SQL Checks

```sql
-- Congress
SELECT congress_number, COUNT(*) FROM congress.bills GROUP BY congress_number ORDER BY congress_number;
SELECT COUNT(*) FROM congress.hearings;

-- OpenStates
SELECT jurisdiction_id, COUNT(*) FROM openstates.bills GROUP BY jurisdiction_id;

-- GovInfo
SELECT code, package_count FROM govinfo.collections;
```

## Troubleshooting

### API Rate Limiting
All CLIs implement automatic rate limiting and exponential backoff. If you see:
```
🐌 Rate limiting active for <api> - waiting for tokens...
```
This is normal. The CLI will automatically wait and retry.

### Database Connection Errors
Ensure PostgreSQL is running and `.env` has correct credentials:
```bash
# Check DB connection
psql -h /var/run/postgresql -d opendiscourse -c "SELECT version();"
```

### Missing API Keys
Verify all keys are loaded:
```bash
python3 -c "from scripts.utils import resource_manager; print(resource_manager.CONGRESS_API_KEY)"
```

## Performance Tips

1. **Use Dry Run First**: Test with `--dry-run` before large ingestions
2. **Monitor Logs**: Watch `logs/20_year_ingestion.log` for errors
3. **Database Indexing**: Ensure migrations are applied for optimal performance
4. **Parallel Execution**: The 20-year script uses 20 workers by default
5. **Rate Limits**: Default limits are conservative; adjust in `config/ingestion_config.yaml` if needed

## Schema Reference

All tables are documented in:
- `migrations/001_congress_schema.sql`
- `migrations/015_congress_extended_schema.sql`
- `migrations/002_govinfo_schema.sql`
- `migrations/003_openstates_schema_optimized.sql`
