# Feature Specifications
## OpenDiscourse CLI Tools v2.0

---

## 1. Enhanced Filtering & Slicing

### 1.1 Date Range Filtering
**All CLIs**

```bash
# Single date
opendiscourse-congress bills --since 2024-01-01

# Date range
opendiscourse-congress bills --from 2023-01-01 --to 2024-12-31

# Relative dates
opendiscourse-congress bills --last-30-days
opendiscourse-congress bills --this-year
opendiscourse-congress bills --last-congress
```

### 1.2 Field-Based Filtering
**Congress CLI**

```bash
# Single field
opendiscourse-congress bills --sponsor "Smith"

# Multiple fields (AND)
opendiscourse-congress bills --sponsor "Smith" --party "D" --state "CA"

# OR logic
opendiscourse-congress bills --party "D,R,I"

# NOT logic
opendiscourse-congress bills --not-state "CA,NY,TX"

# Numeric ranges
opendiscourse-congress bills --cosponsors-min 100 --cosponsors-max 500
```

### 1.3 Full-Text Search
**All CLIs**

```bash
# Simple search
opendiscourse-congress bills --search "climate change"

# Advanced search with operators
opendiscourse-congress bills --search "climate AND (renewable OR solar)"

# Field-specific search
opendiscourse-congress bills --title-contains "infrastructure"
```

---

## 2. Export Capabilities

### 2.1 Multiple Formats

```bash
# JSON (default)
opendiscourse-congress bills --congress 118 --format json

# JSON Lines (streaming-friendly)
opendiscourse-congress bills --congress 118 --format jsonl

# CSV
opendiscourse-congress bills --congress 118 --format csv

# Parquet (columnar)
opendiscourse-congress bills --congress 118 --format parquet

# SQLite (portable database)
opendiscourse-congress bills --congress 118 --format sqlite --output bills.db
```

### 2.2 Compression

```bash
# Gzip
opendiscourse-congress bills --congress 118 --compress gzip

# Brotli (better compression)
opendiscourse-congress bills --congress 118 --compress br

# Auto-detect from filename
opendiscourse-congress bills --congress 118 --output bills.json.gz
```

### 2.3 Column Selection

```bash
# Specific columns
opendiscourse-congress bills --columns bill_number,title,sponsor

# Exclude columns
opendiscourse-congress bills --exclude-columns full_text,metadata
```

---

## 3. Query Builder

### 3.1 Interactive Mode

```bash
# Launch interactive query builder
opendiscourse-congress query

# Example interactive session:
> Select data type: bills
> Filter by congress: 118
> Filter by party: D,R
> Export format: csv
> Output file: bills_118.csv
> Execute? [y/N]: y
```

### 3.2 SQL-Like Queries

```bash
# Direct SQL queries (read-only)
opendiscourse-congress sql "SELECT bill_type, COUNT(*) FROM congress.bills GROUP BY bill_type"

# Parameterized queries
opendiscourse-congress sql --params congress=118 "SELECT * FROM congress.bills WHERE congress_number = :congress"
```

---

## 4. Analysis Features

### 4.1 Summary Statistics

```bash
# Bill statistics
opendiscourse-congress stats bills --congress 118
# Output:
# Total: 12,345
# By Type: HR: 8,234 | S: 3,456 | ...
# By Status: Enacted: 234 | Failed: 567 | ...

# Voting analysis
opendiscourse-congress stats votes --congress 118
# Output:
# Total Votes: 890
# Party Unity: D: 92% | R: 88%
# Bipartisan: 234 votes
```

### 4.2 Trending Analysis

```bash
# Most active sponsors
opendiscourse-congress trends sponsors --congress 118 --limit 10

# Most common subjects
opendiscourse-congress trends subjects --congress 118

# Committee activity
opendiscourse-congress trends committees --congress 118
```

### 4.3 Comparison Features

```bash
# Compare across congresses
opendiscourse-congress compare --congresses 117,118 --metric bills-introduced

# Compare across states
opendiscourse-states compare --states ca,tx,ny --metric bills-passed

# Diff two datasets
opendiscourse-congress diff bills.json bills_updated.json
```

---

## 5. Incremental Sync

### 5.1 Delta Ingestion

```bash
# Sync only new/updated records
opendiscourse-congress sync bills --congress 118

# Sync with custom checkpoint
opendiscourse-congress sync bills --since-checkpoint 2024-12-01T00:00:00Z

# Continuous sync (daemon mode)
opendiscourse-congress sync bills --watch --interval 3600
```

### 5.2 Checkpoint Management

```bash
# List checkpoints
opendiscourse-congress checkpoints list

# Create checkpoint
opendiscourse-congress checkpoints create --name "before-major-sync"

# Restore from checkpoint
opendiscourse-congress checkpoints restore --name "before-major-sync"
```

---

## 6. Advanced Configuration

### 6.1 Configuration Profiles

```bash
# Create config profile
opendiscourse-congress config init --profile production

# Use profile
opendiscourse-congress --profile production bills --congress 118

# List profiles
opendiscourse-congress config list
```

### 6.2 Environment-Specific Settings

```yaml
# ~/.config/opendiscourse/congress.yaml
profiles:
  development:
    database:
      host: localhost
      name: opendiscourse_dev
    api:
      rate_limit: 10

  production:
    database:
      host: prod-db.example.com
      name: opendiscourse
    api:
      rate_limit: 100
```

---

## 7. Pipeline Integration

### 7.1 Streaming Output

```bash
# Stream to stdout (pipe-friendly)
opendiscourse-congress bills --congress 118 --format jsonl --stream | \
  jq -r '.title' | \
  head -10

# Progress to stderr, data to stdout
opendiscourse-congress bills --congress 118 --quiet --format csv > bills.csv
```

### 7.2 Webhook Support

```bash
# Send to webhook on completion
opendiscourse-congress bills --congress 118 --webhook https://example.com/notify

# Custom webhook payload
opendiscourse-congress bills --congress 118 --webhook-template webhook.json
```

---

## 8. Monitoring & Observability

### 8.1 Metrics Export

```bash
# Prometheus metrics endpoint
opendiscourse-congress serve-metrics --port 9090

# Export metrics to file
opendiscourse-congress metrics export --format prometheus --output metrics.txt
```

### 8.2 Structured Logging

```bash
# JSON logs
opendiscourse-congress --log-format json bills --congress 118

# Different log levels
opendiscourse-congress --log-level debug bills --congress 118

# Log to file
opendiscourse-congress --log-file ingestion.log bills --congress 118
```

---

## 9. Validation & Quality

### 9.1 Data Validation

```bash
# Validate before export
opendiscourse-congress bills --congress 118 --validate --format csv

# Schema validation
opendiscourse-congress validate-schema --file bills.csv --schema bills.schema.json

# Data quality report
opendiscourse-congress quality-check --table congress.bills
```

### 9.2 Dry Run Mode

```bash
# Simulate without changes
opendiscourse-congress bills --congress 118 --dry-run

# Show SQL that would be executed
opendiscourse-congress bills --congress 118 --explain
```

---

## 10. Developer Features

### 10.1 Debug Mode

```bash
# Verbose output
opendiscourse-congress -vvv bills --congress 118

# HTTP request logging
opendiscourse-congress --debug-http bills --congress 118

# Performance profiling
opendiscourse-congress --profile bills --congress 118
```

### 10.2 API Testing

```bash
# Test API connectivity
opendiscourse-congress test-connection

# Benchmark API performance
opendiscourse-congress benchmark --endpoint bills --requests 100

# Mock mode (for testing)
opendiscourse-congress --mock bills --congress 118
```

---

## 11. Batch Operations

### 11.1 Parallel Execution

```bash
# Process multiple congresses in parallel
opendiscourse-congress bills --congresses 115,116,117,118 --parallel 4

# Process all states in parallel
opendiscourse-states bills --all-states --parallel 10
```

### 11.2 Job Scheduling

```bash
# Schedule recurring ingestion
opendiscourse-congress schedule add \
  --name "daily-sync" \
  --cron "0 2 * * *" \
  --command "sync bills --congress 118"

# List scheduled jobs
opendiscourse-congress schedule list

# Run job immediately
opendiscourse-congress schedule run daily-sync
```

---

## 12. Security Features

### 12.1 API Key Management

```bash
# Store API key securely
opendiscourse-congress auth login

# Use keyring
opendiscourse-congress auth set-keyring

# Rotate keys
opendiscourse-congress auth rotate
```

### 12.2 Data Encryption

```bash
# Encrypt exports
opendiscourse-congress bills --congress 118 --encrypt --key ~/.ssh/public.key

# Decrypt
opendiscourse-congress decrypt bills.json.enc --key ~/.ssh/private.key
```

---

## Feature Priority Matrix

| Feature | Priority | Complexity | Impact |
|---------|----------|------------|--------|
| Multi-format export | High | Medium | High |
| Advanced filtering | High | Medium | High |
| Incremental sync | High | High | High |
| Query builder | Medium | High | Medium |
| Analysis features | Medium | Medium | High |
| Pipeline integration | Medium | Low | Medium |
| Batch operations | Low | Medium | Medium |
| Security features | Low | Low | Low |
