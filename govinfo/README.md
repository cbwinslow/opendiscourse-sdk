# GovInfo Data Integration Toolkit

This directory packages reference materials, database migrations, and ingestion
utilities for working with the [govinfo.gov](https://www.govinfo.gov) API and
bulk data services. It is designed to support the OpenDiscourse ingestion
pipeline by delivering a comprehensive relational model and high-throughput
download tooling for legislative, voting, and membership datasets.

## Contents

- `usgpo-api/` – shallow clone of the official [`usgpo/api`](https://github.com/usgpo/api)
  repository describing the public API and providing request samples.
- `sql/` – PostgreSQL migrations that provision a `govinfo` schema with tables,
  constraints, and indexes covering bills, bill summaries, voting records,
  membership relationships, and download metadata.
- `scripts/` – asynchronous ingestion orchestration capable of streaming data
  from both the GovInfo REST API and bulk archives with GPU-assisted processing
  when available.

## Running the migrations

The migration files are ordered and idempotent so they can be executed with any
standard tool (psql, Alembic, dbmate, etc.). Example:

```bash
psql "$DATABASE_URL" -f sql/001_create_tables.sql
psql "$DATABASE_URL" -f sql/002_indexes.sql
```

The schema includes:

- Publication metadata (`collections`, `packages`, `granules`, `bulk_packages`)
- Legislative content (`bills`, `bill_versions`, `bill_summaries`, `bill_actions`,
  `bill_committees`, `bill_cosponsors`, `bill_subjects`, `bill_amendments`)
- Voting detail (`votes`, `vote_actions`, `vote_totals`, `vote_ballots`)
- Membership analytics (`members`, `member_terms`, `memberships`,
  `member_votes`, `member_attendance`, `membership_votes`, `membership_attendance`,
  `membership_bills`, `member_bill_positions`, `attendance_records`)

## Ingestion orchestration

`scripts/ingest_govinfo.py` uses `asyncio`, `aiohttp`, GPU memory copies (via
`cupy` when installed), and thread offloading to accelerate large scale
downloads. Key features include:

- Concurrent pagination of API collections with configurable sampling limits
- Parallel traversal and download of the bulk archive hierarchy
- Optional ingestion into PostgreSQL via `asyncpg` with robust upserts against
  the schema defined above
- JSONL artifact generation for offline inspection

### Quick start

```bash
python scripts/ingest_govinfo.py \
  --api-key "$GOVINFO_API_KEY" \
  --collections BILLS,BILLSTATUS,BILLSTATUSXML \
  --bulk-collections BILLS,BILLSTATUS,VOTES \
  --output-dir data/govinfo_ingest \
  --pg-dsn postgresql://user:pass@localhost:5432/opendiscourse
```

Use `--bulk-sample` or `--max-packages` to limit processing for smoke tests.
`--disable-api` and `--disable-bulk` can be combined to focus on a single data
source.

## GPU acceleration

GPU offloading is optional. When `cupy` is present the ingestion script routes
large payloads through GPU memory to accelerate checksum and copy operations.
The pipeline gracefully falls back to CPU-only execution when GPU resources are
unavailable.

## Testing tips

- The API requires an [api.data.gov](https://api.data.gov) key. Export it as
  `GOVINFO_API_KEY` for convenience.
- Run the ingestion in `--dry-run` mode to skip database writes while still
  verifying download throughput.
- Materialized views and indexes in `002_indexes.sql` can be refreshed or
  re-run without dropping tables to keep analytical summaries up to date.
