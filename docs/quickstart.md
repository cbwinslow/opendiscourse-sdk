# Quick Start Guide
## Get Up and Running in 5 Minutes

This guide will get you from zero to ingesting congressional data in just a few minutes.

---

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- API keys for data sources (free to obtain)

---

## Step 1: Install

```bash
# Clone the repository
git clone https://github.com/cbwinslow/opendiscourse.git
cd opendiscourse

# Install in development mode
pip install -e .
```

**Note:** This installs the package with all dependencies including:
- pydantic & pydantic-settings (configuration)
- click & rich (CLI framework)
- psycopg2-binary (PostgreSQL)
- requests (API clients)

---

## Step 2: Get API Keys

### Congress.gov API
1. Visit https://api.congress.gov/sign-up/
2. Sign up with your email
3. Copy your API key

### OpenStates API
1. Visit https://openstates.org/accounts/profile/
2. Create a free account
3. Generate an API key

### GovInfo API
1. Visit https://api.govinfo.gov/auth/
2. Sign up with your email
3. Copy your API key

---

## Step 3: Configure

```bash
# Create .env file from template
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

**Minimum Required Settings:**
```bash
# Database
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__NAME=opendiscourse
DATABASE__USER=your_username
# DATABASE__PASSWORD=your_password  # Optional if using peer authentication

# API Keys
CONGRESS_API__API_KEY=your_congress_api_key_here
OPENSTATES_API__API_KEY=your_openstates_api_key_here
GOVINFO_API__API_KEY=your_govinfo_api_key_here
```

---

## Step 4: Bootstrap Database

```bash
# Interactive setup
opendiscourse bootstrap

# This will:
# 1. Test PostgreSQL connection
# 2. Create database if needed
# 3. Apply all migrations
# 4. Verify setup
```

**Example Output:**
```
==============================================================
OpenDiscourse Database Bootstrap
==============================================================

Step 1: Testing PostgreSQL connection...
✅ PostgreSQL server connection successful

Step 2: Checking database status...
⚠️  Database 'opendiscourse' does not exist
Create database 'opendiscourse'? [Y/n]: y

Step 3: Running bootstrap...
📊 Creating database 'opendiscourse'...
✅ Database created successfully
📦 Found 15 pending migration(s)
📝 Applying migrations...
✅ Bootstrap Complete!
```

---

## Step 5: Verify Setup

```bash
# Run system verification
opendiscourse verify
```

**Expected Output:**
```
OpenDiscourse System Verification

✓ Configuration system: OK
✓ Database connection: OK
✓ Congress API key: Configured
✓ OpenStates API key: Configured
✓ GovInfo API key: Configured

✓ System verification complete!
```

---

## Step 6: Start Ingesting Data

### Option A: Interactive Unified CLI (Recommended)

```bash
# Ingest bills from current Congress
opendiscourse congress bills 118

# Ingest California state bills (last 5 years)
opendiscourse states bills ca --years-back 5

# Ingest GovInfo collections
opendiscourse govinfo collections
```

### Option B: Individual CLI Commands

```bash
# Congress.gov
opendiscourse-congress ingest-bills 118
opendiscourse-congress ingest-members 118
opendiscourse-congress ingest-votes 118

# OpenStates
opendiscourse-states ingest-bills ca --years-back 5
opendiscourse-states ingest-people ca

# GovInfo
opendiscourse-govinfo list-collections
opendiscourse-govinfo ingest-collection BILLS --start-date 2024-01-01
```

---

## Common Tasks

### Ingest Historical Data

```bash
# Last 10 congresses (20 years)
for congress in {109..118}; do
  opendiscourse congress bills $congress
done

# Multiple states
for state in ca ny tx fl; do
  opendiscourse states bills $state --years-back 10
done
```

### Check Ingestion Progress

```bash
# Connect to database
psql opendiscourse

# Check bill counts
SELECT
  congress_number,
  COUNT(*) as bill_count
FROM congress.bills
GROUP BY congress_number
ORDER BY congress_number DESC;

# Check state bill counts
SELECT
  jurisdiction_id,
  COUNT(*) as bill_count
FROM openstates.bills
GROUP BY jurisdiction_id
ORDER BY bill_count DESC;
```

### Export Data

```bash
# Export to CSV
psql opendiscourse -c "\COPY congress.bills TO 'bills.csv' CSV HEADER"

# Export to JSON
psql opendiscourse -c "SELECT json_agg(bills) FROM congress.bills" > bills.json
```

---

## Dry Run Mode

Test without making changes:

```bash
# Add --dry-run flag
opendiscourse congress bills 118 --dry-run
opendiscourse states bills ca --dry-run
```

---

## Troubleshooting

### "pydantic not found"

```bash
pip install pydantic pydantic-settings
```

### "Database connection failed"

Check your database settings:
```bash
# Test PostgreSQL connection
psql -h localhost -U your_username -d postgres

# Check .env file
cat .env | grep DATABASE
```

### "API key not configured"

Make sure your .env file has the correct format:
```bash
# Correct (double underscore for nested config)
CONGRESS_API__API_KEY=your_key_here

# Incorrect (single underscore)
CONGRESS_API_KEY=your_key_here  # Won't work with Pydantic
```

### "Schema not found"

```bash
# Re-run bootstrap
opendiscourse bootstrap
```

---

## Next Steps

- **Explore More Endpoints**: See `docs/cli_documentation.md` for all available commands
- **Advanced Filtering**: Check `docs/features.md` for filtering options
- **Export Data**: Learn about multi-format export in `docs/configuration.md`
- **Automate**: Set up cron jobs or systemd timers for regular updates

---

## Getting Help

```bash
# General help
opendiscourse --help

# Command-specific help
opendiscourse congress --help
opendiscourse congress bills --help

# Verify system
opendiscourse verify
```

---

**🎉 Congratulations! You're now ingesting legislative data!**

Check out the full documentation in the `docs/` directory for advanced features.
