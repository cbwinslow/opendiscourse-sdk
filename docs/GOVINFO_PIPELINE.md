# GovInfo Data Pipeline

## Overview

The GovInfo data pipeline provides automated download, processing, and validation of government documents from the GovInfo API. This pipeline handles various document collections including Bills, Congressional Records, Federal Register, and more.

## Features

- ✅ Automated data download from GovInfo API
- ✅ Multi-format document support (XML, HTML, PDF)
- ✅ Data validation and quality checks
- ✅ Structured data transformation
- ✅ Error handling and retry logic
- ✅ Progress tracking and logging
- ✅ Database schema design
- ✅ ERD documentation

## Architecture

```
┌──────────────────┐
│   GovInfo API    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Download Script │ (download_data.py)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Raw Data       │ (data/raw/govinfo/)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Processing Script│ (process_data.py)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Processed Data   │ (data/processed/govinfo/)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│Validation Script │ (validate_data.py)
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
- GovInfo API key (obtain from https://www.govinfo.gov/api)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOVINFO_API_KEY

# Create data directories
mkdir -p data/raw/govinfo data/processed/govinfo
```

## Usage

### 1. Download Data

Download government documents from GovInfo API:

```bash
# Download bills from 118th Congress
python download_data.py --collection BILLS --congress 118

# Download with date range
python download_data.py --collection BILLS --start-date 2024-01-01 --end-date 2024-12-31

# Download multiple collections
python download_data.py --collection BILLS,CREC --congress 118

# Show all available options
python download_data.py --help
```

**Options:**
- `--collection`: Collection code (BILLS, CREC, FR, etc.)
- `--congress`: Congress number (e.g., 118)
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--output`: Output directory (default: data/raw/govinfo)
- `--api-key`: GovInfo API key (or set GOVINFO_API_KEY env var)

### 2. Process Data

Transform raw data into structured format:

```bash
# Process all files in raw directory
python process_data.py --input data/raw/govinfo --output data/processed/govinfo

# Process specific collection
python process_data.py --input data/raw/govinfo/BILLS --output data/processed/govinfo

# Enable verbose logging
python process_data.py --input data/raw/govinfo --output data/processed/govinfo --verbose
```

**What it does:**
- Parses XML/HTML/JSON files
- Extracts metadata and content
- Standardizes data structure
- Generates summary reports

### 3. Validate Data

Ensure data quality and completeness:

```bash
# Validate processed data
python validate_data.py --input data/processed/govinfo

# Show detailed validation report
python validate_data.py --input data/processed/govinfo --verbose

# Generate validation report only
python validate_data.py --input data/processed/govinfo --report-only
```

**Validation checks:**
- Required fields present
- Data format correctness
- Cross-reference consistency
- URL accessibility
- File integrity

### 4. Advanced Ingestion

Use the advanced ingestion pipeline for production:

```bash
# Run full ingestion pipeline
python scripts/govinfo_ingestor.py --collection BILLS --congress 118

# Ingest with database loading
python scripts/govinfo_ingestor.py \
  --collection BILLS \
  --congress 118 \
  --database-url postgresql://user:pass@localhost/opendiscourse
```

## Data Structure

### Raw Data Format

Downloaded files are organized by collection and date:

```
data/raw/govinfo/
├── BILLS/
│   ├── 118/
│   │   ├── hr1234/
│   │   │   ├── metadata.json
│   │   │   ├── content.xml
│   │   │   └── document.pdf
│   │   └── ...
│   └── ...
└── CREC/
    └── ...
```

### Processed Data Format

Processed data is standardized JSON:

```json
{
  "document_id": "BILLS-118hr1234",
  "collection": "BILLS",
  "congress": 118,
  "doc_type": "hr",
  "doc_number": "1234",
  "title": "Example Bill Title",
  "date_issued": "2024-01-15",
  "metadata": {
    "sponsors": [...],
    "cosponsors": [...],
    "committees": [...]
  },
  "content": {
    "text": "Full bill text...",
    "sections": [...]
  },
  "urls": {
    "content": "https://...",
    "pdf": "https://...",
    "xml": "https://..."
  }
}
```

## Database Schema

See [govinfo_schema.puml](erd/govinfo_schema.puml) for the Entity-Relationship Diagram.

### Main Tables

- **documents**: Core document information
- **collections**: Available GovInfo collections
- **congress_sessions**: Congressional session data
- **document_content**: Full text content
- **document_metadata**: Extended metadata
- **download_log**: Download history
- **processing_log**: Processing history

### Example Schema Creation

```sql
-- Create documents table
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    collection VARCHAR(50) NOT NULL,
    congress INTEGER,
    doc_type VARCHAR(50),
    doc_number VARCHAR(50),
    title TEXT,
    date_issued DATE,
    package_id VARCHAR(100),
    content_url TEXT,
    pdf_url TEXT,
    raw_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_documents_collection ON documents(collection);
CREATE INDEX idx_documents_congress ON documents(congress);
CREATE INDEX idx_documents_date ON documents(date_issued);
```

## Available Collections

| Code | Description |
|------|-------------|
| BILLS | Bills and Resolutions |
| CREC | Congressional Record |
| FR | Federal Register |
| CFR | Code of Federal Regulations |
| STATUTE | Statutes at Large |
| USCODE | United States Code |
| CHRG | Congressional Hearings |
| CRPT | Committee Reports |

## Error Handling

The pipeline includes comprehensive error handling:

- **Network errors**: Automatic retry with exponential backoff
- **API errors**: Error logging and notification
- **Parsing errors**: Skip corrupted files, log errors
- **Validation errors**: Detailed error reports

## Performance

### Optimization Tips

1. **Parallel Processing**: Use `--workers` flag for concurrent downloads
2. **Incremental Updates**: Use date ranges to download only new data
3. **Batch Processing**: Process files in batches to manage memory
4. **Database Indexing**: Create appropriate indexes for query performance

### Benchmarks

- Download speed: ~100-500 documents/hour (depends on document size)
- Processing speed: ~1000-5000 documents/hour
- Validation speed: ~5000-10000 documents/hour

## Monitoring

### Log Files

Logs are written to:
- `logs/download.log`: Download activity
- `logs/process.log`: Processing activity
- `logs/validate.log`: Validation results

### Progress Reports

Each script generates progress reports:
- Download summary: `data/raw/govinfo/download_summary.json`
- Processing summary: `data/processed/govinfo/processing_summary.json`
- Validation report: `data/processed/govinfo/validation_report.json`

## Troubleshooting

### Common Issues

**Issue: API rate limiting**
```bash
# Solution: Add delay between requests
python download_data.py --rate-limit 1.0  # 1 second between requests
```

**Issue: Incomplete downloads**
```bash
# Solution: Resume from last checkpoint
python download_data.py --resume
```

**Issue: Memory errors during processing**
```bash
# Solution: Process in smaller batches
python process_data.py --batch-size 100
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to this pipeline.

## API Documentation

For detailed API documentation, see:
- [GovInfo API Documentation](https://www.govinfo.gov/api)
- [OpenDiscourse API Docs](../docs/api/)

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
