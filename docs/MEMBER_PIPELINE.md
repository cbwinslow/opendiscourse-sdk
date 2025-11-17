# Member Data Pipeline

## Overview

The Member data pipeline provides automated download, processing, and validation of congressional member information. This pipeline handles biographical data, terms of service, party affiliations, leadership roles, and contact information for all members of Congress.

## Features

- ✅ Congress API integration
- ✅ Automated data download
- ✅ Historical data retrieval (back to 94th Congress)
- ✅ Data validation and quality checks
- ✅ Structured data transformation
- ✅ Term tracking across congresses
- ✅ Party affiliation history
- ✅ Leadership role tracking
- ✅ Social media profiles
- ✅ ERD documentation

## Architecture

```
┌──────────────────┐
│  Congress API    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Download Script │ (download_member_data.py)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Raw Data       │ (data/raw/members/)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Processing Script│ (process_member_data.py)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Processed Data   │ (data/processed/members/)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│Validation Script │ (validate_member_data.py)
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
mkdir -p data/raw/members data/processed/members
```

## Usage

### 1. Download Data

Download member information from Congress API:

```bash
# Download all current members
python download_member_data.py --output data/raw/members

# Download specific congress
python download_member_data.py --congress 118 --output data/raw/members

# Download historical data
python download_member_data.py \
  --congress-start 94 \
  --congress-end 118 \
  --output data/raw/members

# Download specific chamber
python download_member_data.py --chamber house --output data/raw/members

# Show all available options
python download_member_data.py --help
```

**Options:**
- `--congress`: Single congress number (e.g., 118)
- `--congress-start`: Start of congress range
- `--congress-end`: End of congress range
- `--chamber`: Chamber (house, senate, or both)
- `--current-only`: Only download current members
- `--output`: Output directory (default: data/raw/members)
- `--api-key`: Congress API key (or set CONGRESS_API_KEY env var)

### 2. Process Data

Transform raw data into structured format:

```bash
# Process all member files
python process_member_data.py \
  --input data/raw/members \
  --output data/processed/members

# Process with historical aggregation
python process_member_data.py \
  --input data/raw/members \
  --output data/processed/members \
  --aggregate-history

# Enable verbose logging
python process_member_data.py \
  --input data/raw/members \
  --output data/processed/members \
  --verbose
```

**What it does:**
- Parses JSON member data
- Extracts biographical information
- Structures term history
- Maps party affiliations
- Tracks leadership roles
- Aggregates social media profiles
- Generates summary reports

### 3. Validate Data

Ensure data quality and completeness:

```bash
# Validate processed data
python validate_member_data.py --input data/processed/members

# Show detailed validation report
python validate_member_data.py --input data/processed/members --verbose

# Validate relationships
python validate_member_data.py \
  --input data/processed/members \
  --check-history
```

**Validation checks:**
- Required fields present
- Bioguide ID format
- Name completeness
- Party code validity
- Chamber values
- State code format
- Date consistency
- Contact information format
- Social media profiles

## Data Structure

### Raw Data Format

Downloaded files are organized by congress and chamber:

```
data/raw/members/
├── 118/
│   ├── house/
│   │   ├── T000478.json     # Rep. Tenney
│   │   ├── A000148.json     # Rep. Adams
│   │   └── ...
│   └── senate/
│       ├── S001203.json     # Sen. Smith
│       └── ...
├── 117/
│   └── ...
└── metadata/
    └── download_info.json
```

### Processed Data Format

Processed data is standardized JSON:

```json
{
  "bioguide_id": "T000478",
  "name": {
    "first": "Claudia",
    "middle": "",
    "last": "Tenney",
    "suffix": "",
    "official": "Claudia Tenney",
    "direct_order": "Tenney, Claudia"
  },
  "party": {
    "code": "R",
    "name": "Republican",
    "history": [
      {
        "party": "Republican",
        "start_date": "2021-01-03",
        "end_date": null
      }
    ]
  },
  "state": "NY",
  "district": 24,
  "terms": [
    {
      "congress": 118,
      "chamber": "House",
      "start_date": "2023-01-03",
      "end_date": "2025-01-03",
      "state": "NY",
      "district": 24,
      "party": "Republican"
    }
  ],
  "congressional_service": {
    "start": "2017-01-03",
    "end": null,
    "years": 6.8
  },
  "current_member": true,
  "leadership_roles": [],
  "contact": {
    "address": "2435 Rayburn House Office Building",
    "phone": "(202) 225-3665",
    "website": "https://tenney.house.gov"
  },
  "social_media": {
    "twitter": "@RepTenney",
    "facebook": "RepClaudiaTenney",
    "youtube": "RepClaudiaTenney"
  },
  "biographical": {
    "birth_year": 1961,
    "death_year": null,
    "image_url": "https://...",
    "biographical_text": "..."
  }
}
```

## Database Schema

See [member_schema.puml](erd/member_schema.puml) for the Entity-Relationship Diagram.

### Main Tables

- **members**: Core member information and biographical data
- **member_terms**: Congressional terms served
- **party_affiliations**: Party history over time
- **leadership_roles**: Leadership positions held
- **member_contact**: Contact information with history
- **member_social_media**: Social media profiles
- **congressional_service**: Aggregated service statistics
- **member_offices**: District and Washington offices

### Example Schema Creation

```sql
-- Create members table
CREATE TABLE members (
    bioguide_id VARCHAR(7) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    suffix VARCHAR(20),
    official_name VARCHAR(200),
    direct_order_name VARCHAR(200),
    birth_year INTEGER,
    death_year INTEGER,
    image_url TEXT,
    biographical_text TEXT,
    current_member BOOLEAN DEFAULT FALSE,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create member_terms table
CREATE TABLE member_terms (
    term_id UUID PRIMARY KEY,
    bioguide_id VARCHAR(7) NOT NULL,
    congress_number INTEGER NOT NULL,
    chamber VARCHAR(20) NOT NULL,
    state VARCHAR(2) NOT NULL,
    district INTEGER,
    party_code VARCHAR(10) NOT NULL,
    party_name VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bioguide_id) REFERENCES members(bioguide_id)
);

-- Create indexes
CREATE INDEX idx_members_name ON members(last_name, first_name);
CREATE INDEX idx_members_current ON members(current_member);
CREATE INDEX idx_terms_bioguide ON member_terms(bioguide_id);
CREATE INDEX idx_terms_congress ON member_terms(congress_number);
CREATE INDEX idx_terms_chamber ON member_terms(chamber);
CREATE INDEX idx_terms_state ON member_terms(state);
```

## Bioguide ID Format

The Bioguide ID is a unique identifier for each member:
- Format: One letter + 6 digits (e.g., `T000478`)
- First letter: Usually last name initial
- Numbers: Sequential assignment
- Persistent across all terms of service

## Data Fields

### Required Fields

- **bioguide_id**: Unique identifier
- **name**: At least first or last name
- **party**: Current party affiliation
- **state**: State represented
- **chamber**: House or Senate

### Optional Fields

- **district**: Required for House members
- **birth_year**: Year of birth
- **death_year**: Year of death (if applicable)
- **image_url**: Official portrait
- **biographical_text**: Biographical narrative
- **social_media**: Social media handles
- **contact**: Contact information
- **leadership_roles**: Leadership positions

## Historical Coverage

The pipeline can retrieve data back to the 94th Congress (1975-1977):

```bash
# Download all historical data
python download_member_data.py \
  --congress-start 94 \
  --congress-end 118 \
  --output data/raw/members/historical

# This covers:
# - 94th Congress (1975-1977) to present
# - ~50 years of congressional history
# - Thousands of members across both chambers
```

## Party Codes

| Code | Party Name |
|------|------------|
| D | Democratic |
| R | Republican |
| I | Independent |
| L | Libertarian |
| G | Green |

## Chamber Values

| Value | Description |
|-------|-------------|
| House | U.S. House of Representatives |
| Senate | U.S. Senate |

## State Codes

Standard two-letter state abbreviations (e.g., NY, CA, TX)

## Advanced Features

### Term Analysis

Analyze member terms and service:

```python
# Get all terms for a member
terms = get_member_terms("T000478")

# Calculate total service years
service_years = calculate_service_years("T000478")

# Find members serving in congress
concurrent_members = get_concurrent_members(118)
```

### Party History Tracking

Track party changes over time:

```python
# Get party history
history = get_party_history("T000478")

# Find party switchers
switchers = find_party_switchers(congress=118)

# Analyze party demographics
demographics = analyze_party_demographics(118)
```

### Leadership Analysis

Analyze leadership roles:

```python
# Get leadership roles
roles = get_leadership_roles("T000478")

# Find all leaders in congress
leaders = get_congress_leaders(118)

# Track leadership changes
changes = track_leadership_changes(start_congress=115, end_congress=118)
```

### Social Media Integration

Track social media presence:

```python
# Get social media profiles
profiles = get_social_media("T000478")

# Find members on specific platform
twitter_users = find_members_on_twitter()

# Analyze social media adoption
adoption = analyze_social_media_adoption()
```

## Error Handling

The pipeline includes comprehensive error handling:

- **API errors**: Retry logic with exponential backoff
- **Missing data**: Graceful handling of optional fields
- **Invalid formats**: Data validation and correction
- **Historical gaps**: Interpolation when possible

## Performance

### Benchmarks

- Download speed: ~50-100 members/minute
- Processing speed: ~200-500 members/minute
- Validation speed: ~500-1000 members/minute
- Historical download: ~5-10 congresses/hour

### Optimization Tips

1. **Parallel Downloads**: Use `--workers` flag for concurrent API calls
2. **Incremental Updates**: Only download changed members
3. **Caching**: Cache API responses locally
4. **Batch Processing**: Process multiple files concurrently

## Monitoring

### Log Files

Logs are written to:
- `logs/member_download.log`: Download activity
- `logs/member_process.log`: Processing activity
- `logs/member_validate.log`: Validation results

### Progress Reports

Each script generates progress reports:
- Download summary: `data/raw/members/download_summary.json`
- Processing summary: `data/processed/members/processing_summary.json`
- Validation report: `data/processed/members/validation_report.json`

### Current Status

See `member_todo.md` for remaining tasks:
- ✅ Website Navigation
- ✅ API Integration
- ✅ Download Script
- ✅ Processing Script
- ✅ Validation Script
- ⏳ Database Schema Implementation
- ⏳ Data Loading
- ⏳ ERD Documentation
- ⏳ Complete Documentation

## Troubleshooting

### Common Issues

**Issue: API rate limiting**
```bash
# Solution: Add delays between requests
python download_member_data.py --rate-limit 1.0
```

**Issue: Missing historical data**
```bash
# Solution: Download full historical range
python download_member_data.py --congress-start 94 --congress-end 118
```

**Issue: Incomplete member profiles**
```bash
# Solution: Force re-download with full details
python download_member_data.py --force-refresh --full-details
```

**Issue: Invalid bioguide IDs**
```bash
# Solution: Validate and fix IDs
python validate_member_data.py --fix-bioguide-ids
```

## Integration

### With Committee Pipeline

Member data integrates with committee data:

```python
# Get member's committee assignments
committees = get_member_committees("T000478")

# Find committee members
members = get_committee_members("HSAG")

# Track assignment history
history = get_assignment_history("T000478")
```

### With Bills Pipeline

Track member legislative activity:

```python
# Get member's sponsored bills
bills = get_member_bills("T000478", congress=118)

# Track cosponsorship
cosponsored = get_cosponsored_bills("T000478")

# Analyze voting record
votes = get_member_votes("T000478")
```

## Examples

### Example 1: Current Members Analysis

```python
# Download current members
download_member_data.py --current-only

# Process and analyze
members = load_processed_members()
demographics = analyze_demographics(members)
print(f"Total current members: {len(members)}")
print(f"Party breakdown: {demographics['by_party']}")
print(f"Chamber breakdown: {demographics['by_chamber']}")
```

### Example 2: Historical Trends

```python
# Download historical range
download_member_data.py --congress-start 94 --congress-end 118

# Analyze trends
trends = analyze_historical_trends()
plot_party_balance_over_time(trends)
plot_tenure_trends(trends)
```

### Example 3: State Representation

```python
# Analyze state representation
state_data = get_state_representation("NY", congress=118)
print(f"House members: {state_data['house_count']}")
print(f"Senators: {state_data['senate_count']}")
print(f"Party split: {state_data['party_split']}")
```

## API Documentation

For detailed API documentation, see:
- [Congress API Documentation](https://api.congress.gov/v3/member/)
- [Bioguide Database](https://bioguide.congress.gov)
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
