# OpenDiscourse Data Ingestion Workflows

This directory contains comprehensive workflow documentation for ingesting legislative and government data into your OpenDiscourse SQL database.

## Quick Navigation

### 🎯 Start Here

**New to OpenDiscourse data ingestion?** Start with the master guide:

👉 **[DATA_INGESTION_MASTER.md](DATA_INGESTION_MASTER.md)** - Complete setup workflow covering all data sources

### 📚 Individual Source Guides

Once you've reviewed the master guide, use these detailed guides for each data source:

1. **[CONGRESS_GOV_API_INGESTION.md](CONGRESS_GOV_API_INGESTION.md)**
   - Federal legislative data from Congress.gov API
   - Bills, resolutions, members, and basic voting data
   - Recommended for: Federal legislative tracking

2. **[GOVINFO_API_INGESTION.md](GOVINFO_API_INGESTION.md)**
   - Government publications from GovInfo.gov API
   - Full-text documents, Congressional Record, Federal Register
   - Recommended for: Document analysis and historical research

3. **[OPENSTATES_API_INGESTION.md](OPENSTATES_API_INGESTION.md)**
   - State-level legislative data from OpenStates API
   - State bills, legislators, votes, and committees
   - Recommended for: State legislative tracking across all 50 states

## What You'll Learn

Each guide provides:

- ✅ Step-by-step setup instructions
- ✅ API key registration process
- ✅ SQL migration commands
- ✅ Python script usage examples
- ✅ Database verification queries
- ✅ Troubleshooting common issues
- ✅ Best practices and optimization tips

## Workflow Overview

```
┌─────────────────────────────────────────────────┐
│         DATA_INGESTION_MASTER.md                │
│         (Start Here - Overview)                 │
└─────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Congress.gov │ │  GovInfo.gov │ │  OpenStates  │
│      API     │ │      API     │ │     API      │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
        ┌─────────────────────────────┐
        │  PostgreSQL Database        │
        │  (govinfo schema)           │
        └─────────────────────────────┘
```

## Prerequisites

Before using these workflows, ensure you have:

- **Python 3.13+** installed
- **PostgreSQL 14+** with pgvector extension
- **Database access** with create table permissions
- **Internet connection** for API access
- **API keys** from Congress.gov, GovInfo.gov, and OpenStates

## Quick Start

If you want to get started immediately:

```bash
# 1. Clone the repository
git clone <repository-url>
cd opendiscourse

# 2. Set up Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Create database
createdb opendiscourse

# 4. Run migrations
psql -d opendiscourse -f govinfo/sql/001_create_tables.sql
psql -d opendiscourse -f govinfo/sql/002_indexes.sql

# 5. Get API keys (see individual guides)
# - Congress.gov: https://api.congress.gov/sign-up/
# - GovInfo.gov: https://www.govinfo.gov/developers/api
# - OpenStates: https://openstates.org/api/

# 6. Configure environment
export CONGRESS_API_KEY="your_key"
export GOVINFO_API_KEY="your_key"
export OPENSTATES_API_KEY="your_key"

# 7. Test with sample data
python congress_api_ingest.py --source congress --congress 118 --limit 5
```

For complete instructions, see [DATA_INGESTION_MASTER.md](DATA_INGESTION_MASTER.md).

## Data Sources Comparison

| Feature | Congress.gov | GovInfo.gov | OpenStates |
|---------|-------------|-------------|------------|
| **Scope** | Federal | Federal | State |
| **Bills** | ✅ Metadata | ✅ Full Text | ✅ State Bills |
| **Members** | ✅ Basic | ✅ Detailed | ✅ State Legislators |
| **Votes** | ✅ Basic | ✅ Detailed | ✅ State Votes |
| **Documents** | ❌ | ✅ Multiple Formats | ❌ |
| **Historical Data** | ✅ All Congresses | ✅ Extensive | ✅ Varies by State |
| **Update Frequency** | Daily | Daily | Daily |
| **Rate Limit** | Moderate | 1000/hour | 100/min (free) |
| **API Key** | Required | Required | Required |

## Directory Structure

```
docs/workflows/
├── README.md                          # This file
├── DATA_INGESTION_MASTER.md           # Master workflow guide
├── CONGRESS_GOV_API_INGESTION.md      # Congress.gov guide
├── GOVINFO_API_INGESTION.md           # GovInfo.gov guide
└── OPENSTATES_API_INGESTION.md        # OpenStates guide
```

## Related Documentation

- [BULK_INGESTION_README.md](../../BULK_INGESTION_README.md) - Overview of bulk ingestion features
- [README.md](../../README.md) - Main project README
- [Test Suite](../../tests/test_congress_ingestion.py) - Test cases and examples

## Common Use Cases

### Use Case 1: Track Federal Legislation

**Goal:** Monitor bills in the current Congress

**Workflow:**
1. Follow [CONGRESS_GOV_API_INGESTION.md](CONGRESS_GOV_API_INGESTION.md)
2. Ingest current Congress bills
3. Set up automated daily updates
4. Query database for bill status

### Use Case 2: Analyze Government Documents

**Goal:** Search and analyze full-text government publications

**Workflow:**
1. Follow [GOVINFO_API_INGESTION.md](GOVINFO_API_INGESTION.md)
2. Ingest desired collections (BILLS, CREC, FR)
3. Enable full-text search
4. Build analytics dashboards

### Use Case 3: Compare State Legislation

**Goal:** Track and compare legislation across multiple states

**Workflow:**
1. Follow [OPENSTATES_API_INGESTION.md](OPENSTATES_API_INGESTION.md)
2. Ingest data from target states
3. Set up automated updates
4. Run comparative analysis queries

### Use Case 4: Complete Legislative Database

**Goal:** Build comprehensive database covering federal and state data

**Workflow:**
1. Start with [DATA_INGESTION_MASTER.md](DATA_INGESTION_MASTER.md)
2. Follow all three source-specific guides
3. Set up automated updates for all sources
4. Implement cross-reference queries

## Support

### Getting Help

If you encounter issues:

1. Check the **Troubleshooting** section in each guide
2. Review the [main project documentation](../../README.md)
3. Check [test cases](../../tests/test_congress_ingestion.py) for examples
4. Review API provider documentation (links in each guide)

### Reporting Issues

When reporting issues, please include:

- Which guide you were following
- The exact command or script you ran
- Error messages (full text)
- Your environment (OS, Python version, PostgreSQL version)
- Whether it's a test run or production ingestion

## Contributing

To improve these workflows:

1. Follow the existing documentation style
2. Test all commands before documenting
3. Include troubleshooting for common issues
4. Provide both simple and advanced examples
5. Keep guides focused and concise

## Version History

- **v1.0** (2024) - Initial comprehensive workflow documentation
  - Master workflow guide
  - Congress.gov API guide
  - GovInfo.gov API guide
  - OpenStates API guide

## License

This documentation is part of the OpenDiscourse project. See the main [LICENSE](../../LICENSE) file for details.

---

**Questions?** Start with the [DATA_INGESTION_MASTER.md](DATA_INGESTION_MASTER.md) guide or check the [main README](../../README.md).
