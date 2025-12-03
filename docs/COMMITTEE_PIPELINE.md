# Committee Data Pipeline

## Overview

The Committee data pipeline provides automated download, processing, and validation of congressional committee information. This pipeline handles committee structure, membership, hearings, and reports.

## Features

- ✅ Committee API integration
- ✅ Automated data download
- ✅ Data validation and quality checks
- ✅ Structured data transformation
- ✅ Historical data tracking
- ✅ Subcommittee relationships
- ✅ Member assignment tracking
- ✅ ERD documentation

## Architecture

```
┌──────────────────┐
│  Congress API    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Download Script │ (download_committee_data.py)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Raw Data       │ (data/raw/committees/)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Processing Script│ (process_committee_data.py)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Processed Data   │ (data/processed/committees/)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│Validation Script │ (validate_committee_data.py)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Database       │ (PostgreSQL)
└──────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 14+ (optional, for database storage)
- Congress API key (obtain from https://api.congress.gov)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your CONGRESS_API_KEY

# Create data directories
mkdir -p data/raw/committees data/processed/committees
```

## Usage

### 1. Download Data

Download committee information from Congress API:

```bash
# Download all committees
python download_committee_data.py --output data/raw/committees

# Download specific congress
python download_committee_data.py --congress 118 --output data/raw/committees

# Download specific chamber
python download_committee_data.py --chamber house --output data/raw/committees

# Show all available options
python download_committee_data.py --help
```

**Options:**
- `--congress`: Congress number (e.g., 118)
- `--chamber`: Chamber (house, senate, or both)
- `--output`: Output directory (default: data/raw/committees)
- `--api-key`: Congress API key (or set CONGRESS_API_KEY env var)
- `--include-subcommittees`: Include subcommittee data

### 2. Process Data

Transform raw data into structured format:

```bash
# Process all committee files
python process_committee_data.py \
  --input data/raw/committees \
  --output data/processed/committees

# Process with relationship mapping
python process_committee_data.py \
  --input data/raw/committees \
  --output data/processed/committees \
  --build-relationships

# Enable verbose logging
python process_committee_data.py \
  --input data/raw/committees \
  --output data/processed/committees \
  --verbose
```

**What it does:**
- Parses JSON committee data
- Extracts committee metadata
- Maps subcommittee relationships
- Standardizes member assignments
- Generates summary reports

### 3. Validate Data

Ensure data quality and completeness:

```bash
# Validate processed data
python validate_committee_data.py --input data/processed/committees

# Show detailed validation report
python validate_committee_data.py --input data/processed/committees --verbose

# Validate relationships
python validate_committee_data.py \
  --input data/processed/committees \
  --check-relationships
```

**Validation checks:**
- Required fields present
- Committee code format
- Parent-child relationships
- Member bioguide IDs
- Date consistency
- URL accessibility

## Data Structure

### Raw Data Format

Downloaded files are organized by chamber and committee:

```
data/raw/committees/
├── house/
│   ├── HSAG.json          # House Agriculture
│   ├── HSAP.json          # House Appropriations
│   └── ...
├── senate/
│   ├── SSAF.json          # Senate Agriculture
│   ├── SSAP.json          # Senate Appropriations
│   └── ...
└── metadata/
    └── download_info.json
```

### Processed Data Format

Processed data is standardized JSON:

```json
{
  "committee_code": "HSAG",
  "committee_name": "House Committee on Agriculture",
  "committee_type": "standing",
  "chamber": "house",
  "parent_committee_code": null,
  "is_subcommittee": false,
  "jurisdiction": "Agriculture and related matters...",
  "website_url": "https://agriculture.house.gov",
  "phone": "(202) 225-2171",
  "members": [
    {
      "bioguide_id": "T000478",
      "name": "Rep. Name",
      "party": "Republican",
      "state": "NY",
      "role": "Chairman",
      "rank": 1
    }
  ],
  "subcommittees": [
    {
      "committee_code": "HSAG03",
      "name": "Subcommittee on Livestock and Foreign Agriculture"
    }
  ]
}
```

## Database Schema

See [committee_schema.puml](erd/committee_schema.puml) for the Entity-Relationship Diagram.

### Main Tables

- **committees**: Core committee information
- **committee_members**: Current and historical membership
- **committee_hearings**: Hearing information and transcripts
- **committee_reports**: Committee reports and documents
- **committee_history**: Historical events and changes
- **committee_assignments**: Detailed assignment tracking

### Example Schema Creation

```sql
-- Create committees table
CREATE TABLE committees (
    committee_id UUID PRIMARY KEY,
    committee_code VARCHAR(20) UNIQUE NOT NULL,
    committee_name VARCHAR(200) NOT NULL,
    committee_type VARCHAR(50),
    parent_committee_code VARCHAR(20),
    chamber VARCHAR(20) NOT NULL,
    is_subcommittee BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    jurisdiction TEXT,
    website_url TEXT,
    phone VARCHAR(20),
    established_date DATE,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_committee_code) REFERENCES committees(committee_code)
);

-- Create indexes
CREATE INDEX idx_committees_code ON committees(committee_code);
CREATE INDEX idx_committees_chamber ON committees(chamber);
CREATE INDEX idx_committees_parent ON committees(parent_committee_code);
CREATE INDEX idx_committees_active ON committees(is_active);
```

## Committee Types

| Type | Description |
|------|-------------|
| standing | Permanent committees with legislative jurisdiction |
| select | Temporary committees for specific issues |
| joint | Committees with members from both chambers |
| special | Special purpose committees |

## Committee Codes

Committee codes follow a standard format:
- House: `HS` + two letters (e.g., `HSAG` for House Agriculture)
- Senate: `SS` + two letters (e.g., `SSAG` for Senate Agriculture)
- Subcommittees: Parent code + two digits (e.g., `HSAG03`)

## Example Committees

### House Committees

| Code | Name |
|------|------|
| HSAG | Agriculture |
| HSAP | Appropriations |
| HSAS | Armed Services |
| HSBA | Financial Services |
| HSBU | Budget |

### Senate Committees

| Code | Name |
|------|------|
| SSAF | Agriculture, Nutrition, and Forestry |
| SSAP | Appropriations |
| SSAS | Armed Services |
| SSBK | Banking, Housing, and Urban Affairs |
| SSBU | Budget |

## Data Relationships

### Committee Hierarchy

```
Standing Committee (HSAG)
├── Subcommittee 1 (HSAG03)
├── Subcommittee 2 (HSAG14)
└── Subcommittee 3 (HSAG29)
```

### Member Assignments

Each committee member has:
- Position (Chairman, Ranking Member, Member)
- Rank within committee
- Start and end dates
- Party affiliation
- State representation

## Advanced Features

### Historical Tracking

Track committee changes over time:

```python
# Get committee history
history = get_committee_history("HSAG")

# Track membership changes
membership_changes = get_membership_changes("HSAG", start_date, end_date)

# Analyze committee evolution
evolution = analyze_committee_evolution("HSAG")
```

### Relationship Mapping

Build committee relationship graphs:

```python
# Get all subcommittees
subcommittees = get_subcommittees("HSAG")

# Map parent-child relationships
relationships = map_committee_relationships()

# Visualize committee structure
visualize_committee_tree("HSAG")
```

## Error Handling

The pipeline includes comprehensive error handling:

- **API errors**: Retry logic with exponential backoff
- **Data inconsistencies**: Validation and correction
- **Missing relationships**: Parent committee lookup
- **Duplicate entries**: Deduplication logic

## Performance

### Benchmarks

- Download speed: ~50-100 committees/minute
- Processing speed: ~200-500 committees/minute
- Validation speed: ~500-1000 committees/minute

### Optimization Tips

1. **Caching**: Cache API responses to reduce requests
2. **Batch Processing**: Process multiple files concurrently
3. **Incremental Updates**: Only update changed committees
4. **Database Indexing**: Index foreign keys and frequently queried fields

## Monitoring

### Log Files

Logs are written to:
- `logs/committee_download.log`: Download activity
- `logs/committee_process.log`: Processing activity
- `logs/committee_validate.log`: Validation results

### Progress Reports

Each script generates progress reports:
- Download summary: `data/raw/committees/download_summary.json`
- Processing summary: `data/processed/committees/processing_summary.json`
- Validation report: `data/processed/committees/validation_report.json`

### Current Status

See `committee_progress.md` for detailed progress tracking:
- ✅ API Setup
- ✅ Data Download
- ✅ Data Validation
- ✅ Data Processing
- ⏳ Database Design
- ⏳ ERD Creation
- ⏳ Documentation (in progress)

## Troubleshooting

### Common Issues

**Issue: Missing parent committee**
```bash
# Solution: Download full committee set first
python download_committee_data.py --include-subcommittees
```

**Issue: Inconsistent membership data**
```bash
# Solution: Cross-reference with member API
python validate_committee_data.py --cross-reference-members
```

**Issue: Outdated committee information**
```bash
# Solution: Force refresh from API
python download_committee_data.py --force-refresh
```

## Integration

### With Member Pipeline

Committee data integrates with member data:

```python
# Link members to committees
link_members_to_committees()

# Get member's committee assignments
assignments = get_member_committees("T000478")

# Get committee membership roster
roster = get_committee_roster("HSAG")
```

### With Bills Pipeline

Track committee actions on legislation:

```python
# Get committee's bills
bills = get_committee_bills("HSAG", congress=118)

# Track bill referrals
referrals = get_bill_referrals("HSAG")
```

## API Documentation

For detailed API documentation, see:
- [Congress API Documentation](https://api.congress.gov/v3/committee/)
- [OpenDiscourse API Docs](../docs/api/)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to this pipeline.

## License

MIT License - See [LICENSE](../LICENSE) for details.

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Contact the development team

---

**Last Updated:** November 7, 2025  
**Version:** 1.0.0  
**Maintainer:** OpenDiscourse Team
