# Congress.gov Data Integration Toolkit

This directory contains documentation, database migrations, and ingestion tooling to replicate core
entities exposed by [Congress.gov](https://www.congress.gov/) and its public API at
`https://api.congress.gov/`.

## Contents

- `data_model.md` &mdash; Detailed explanation of the logical data model distilled from the public
  website and API documentation.
- `migrations/` &mdash; PostgreSQL-compatible SQL migration scripts that materialize the schema needed
  to store the Congress.gov dataset.
- `ingest_congress_data.py` &mdash; Asynchronous, GPU-aware ingestion pipeline that streams data from
  the public API into the relational schema. The script supports sampling, parallel downloads, and
  resumable checkpoints for efficient development and production workflows.

## Prerequisites

1. **Database** &mdash; PostgreSQL 14+ with the `pgcrypto` extension enabled (used for UUID generation
   and hashing utilities).
2. **Python environment** &mdash; Python 3.10+ with dependencies listed in the module-level docstring of
   `ingest_congress_data.py`.
3. **Congress.gov API key** &mdash; Request an API key and export it via `CONGRESS_API_KEY` or supply it
   with the `--api-key` command line flag.
4. **GPU acceleration (optional)** &mdash; Install the RAPIDS stack (`cudf`, `cupy`) if a CUDA-capable
   GPU is available. The ingestion pipeline auto-detects GPU libraries and falls back to CPU-only
   processing when they are absent.

## Usage Overview

1. Run the migrations in `migrations/` (in lexical order) against your target PostgreSQL database.
2. Configure access credentials via environment variables or CLI flags.
3. Execute `python ingest_congress_data.py --resource bills` (or any supported resource) to ingest
   records. Use `--sample-size` to limit the number of items while testing.

## Extensibility

The toolkit is intentionally modular. You can:

- Add new SQL migrations to extend the schema when Congress.gov publishes new collections.
- Implement additional resource loaders by subclassing `BaseResourceLoader`.
- Adjust concurrency knobs (`--max-concurrent-requests`, `--thread-pool-size`) to match your
  infrastructure capacity.

