# Complete Members Data Ingestion Guide

## 🎯 Overview

This guide provides complete instructions for ingesting members data from all three data sources with proper deduplication and real-time monitoring.

## 📊 Data Sources & Deduplication Strategy

### Current Status
- **Congress.gov**: ✅ 1,901 members (COMPLETE)
- **GovInfo.gov**: 🔄 0 members (READY FOR INGESTION)  
- **OpenStates.org**: 🔄 0 people (READY FOR INGESTION)

### Deduplication Strategy

Each data source uses different identifier systems:

| Source | Primary Key | Secondary ID | Deduplication Method |
|--------|-------------|-------------|---------------------|
| Congress.gov | `bioguide_id` | - | Primary key constraint |
| GovInfo.gov | `member_id` | `bioguide_id` | Unique constraint on bioguide_id |
| OpenStates.org | `person_id` | - | Primary key constraint |

**Key Insight**: These are **separate data sources** with different identifier systems. Deduplication is maintained **within** each source, not across sources.

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Set API keys in .env file
echo "GOVINFO_API_KEY=your_govinfo_api_key" >> .env
echo "OPENSTATES_API_KEY=your_openstates_api_key" >> .env
echo "CONGRESS_API_KEY=your_congress_api_key" >> .env

# Set database credentials
echo "DB_NAME=cbwinslow" >> .env
echo "DB_USER=cbwinslow" >> .env
```

### 2. Run Setup Script
```bash
# Complete setup and testing
python scripts/setup_members_ingestion.py

# Or run individual components
python scripts/analyze_members_deduplication.py --all
```

### 3. Ingest Data

#### GovInfo Members
```bash
# Dry run test
python scripts/ingest_govinfo_members_monitored.py --dry-run --congress 118

# Actual ingestion with TUI monitoring
python scripts/ingest_govinfo_members_monitored.py --congress 118 --monitor-mode tui

# Batch ingestion for multiple congresses
python scripts/ingest_govinfo_members_monitored.py --congress 118 --batch-size 25 --monitor-mode simple
```

#### OpenStates People
```bash
# Dry run test
python scripts/ingest_openstates_people_monitored.py --dry-run --jurisdiction ca

# Actual ingestion for specific jurisdiction
python scripts/ingest_openstates_people_monitored.py --jurisdiction ca --monitor-mode tui

# Ingest all jurisdictions
python scripts/ingest_openstates_people_monitored.py --monitor-mode simple
```

## 📈 Monitoring Options

### Display Modes
- **TUI Mode**: Rich terminal display with progress bars and real-time metrics
- **Simple Mode**: Text-based progress updates
- **Silent Mode**: Database-only tracking (no console output)

### Monitoring Examples
```bash
# TUI monitoring (best for interactive sessions)
python scripts/ingest_govinfo_members_monitored.py --congress 118 --monitor-mode tui

# Simple monitoring (good for logs)
python scripts/ingest_govinfo_members_monitored.py --congress 118 --monitor-mode simple

# Silent monitoring (for production/automation)
python scripts/ingest_govinfo_members_monitored.py --congress 118 --monitor-mode silent
```

## 🧪 Testing & Validation

### Dry Run Testing
```bash
# Test all scripts with dry runs
python scripts/ingest_govinfo_members_monitored.py --dry-run --congress 118
python scripts/ingest_openstates_people_monitored.py --dry-run --jurisdiction ca
```

### Deduplication Validation
```bash
# Run comprehensive deduplication analysis
python scripts/analyze_members_deduplication.py --all

# Generate detailed report
python scripts/analyze_members_deduplication.py --report

# Validate current data
python scripts/analyze_members_deduplication.py --validate
```

### Data Quality Checks
```bash
# Check data quality after ingestion
python scripts/verify_congress_data.py --check-quality

# View cross-reference analysis
psql -U cbwinslow -d cbwinslow -c "SELECT * FROM analysis.members_cross_reference LIMIT 10;"
```

## 🔧 Advanced Configuration

### Batch Size Optimization
```bash
# Large datasets - use smaller batches
python scripts/ingest_govinfo_members_monitored.py --congress 118 --batch-size 10

# Fast networks - use larger batches  
python scripts/ingest_govinfo_members_monitored.py --congress 118 --batch-size 100
```

### Rate Limiting
```bash
# Conservative rate limiting
python scripts/ingest_govinfo_members_monitored.py --congress 118 --request-delay 1.0

# Aggressive rate limiting (if API allows)
python scripts/ingest_govinfo_members_monitored.py --congress 118 --request-delay 0.1
```

## 📊 Monitoring Database Queries

### Active Jobs
```sql
-- View active ingestion jobs
SELECT * FROM ingestion_jobs WHERE status = 'running' ORDER BY started_at DESC;

-- View job progress
SELECT 
    job_name,
    data_source,
    table_name,
    status,
    total_records,
    processed_records,
    failed_records,
    throughput_per_minute,
    started_at
FROM ingestion_jobs
ORDER BY started_at DESC;
```

### Cross-Reference Analysis
```sql
-- View cross-reference data
SELECT * FROM analysis.members_cross_reference 
WHERE cross_reference_id IS NOT NULL
LIMIT 10;

-- Count cross-references by source
SELECT 
    source_schema,
    COUNT(*) as total,
    COUNT(cross_reference_id) as with_cross_ref
FROM analysis.members_cross_reference
GROUP BY source_schema;
```

## 🚨 Troubleshooting

### Common Issues

#### API Key Errors
```bash
# Check API keys
echo $GOVINFO_API_KEY
echo $OPENSTATES_API_KEY

# Test API connectivity
curl -H "X-API-Key: $GOVINFO_API_KEY" "https://api.govinfo.gov/members?congress=118&pageSize=1"
```

#### Database Connection Issues
```bash
# Test database connection
psql -U cbwinslow -d cbwinslow -c "SELECT 1;"

# Check table existence
psql -U cbwinslow -d cbwinslow -c "\dt govinfo.members"
psql -U cbwinslow -d cbwinslow -c "\dt openstates.people"
```

#### Monitoring Issues
```bash
# Check monitoring tables exist
psql -U cbwinslow -d cbwinslow -c "\dt ingestion_jobs"

# Use simple mode if TUI fails
python scripts/ingest_govinfo_members_monitored.py --congress 118 --monitor-mode simple
```

### Error Recovery
```bash
# Continue from where left off (idempotent ingestion)
python scripts/ingest_govinfo_members_monitored.py --congress 118

# Clean up failed jobs
psql -U cbwinslow -d cbwinslow -c "DELETE FROM ingestion_jobs WHERE status = 'failed';"
```

## 📋 Production Deployment

### Automation Script
```bash
#!/bin/bash
# production_ingestion.sh

echo "🚀 Starting production ingestion..."

# Set environment
export GOVINFO_API_KEY=$GOVINFO_API_KEY
export OPENSTATES_API_KEY=$OPENSTATES_API_KEY

# Run deduplication analysis
python scripts/analyze_members_deduplication.py --validate

# Ingest with silent monitoring
python scripts/ingest_govinfo_members_monitored.py --congress 118 --monitor-mode silent
python scripts/ingest_openstates_people_monitored.py --monitor-mode silent

# Final validation
python scripts/analyze_members_deduplication.py --report

echo "✅ Production ingestion completed!"
```

### Cron Job Setup
```bash
# Add to crontab for daily execution
0 2 * * * cd /path/to/opendiscourse && ./production_ingestion.sh >> /var/log/ingestion.log 2>&1
```

## 🎉 Success Criteria

### Complete Setup When:
- ✅ All API keys are configured
- ✅ Database connections work
- ✅ Deduplication analysis passes
- ✅ Dry run tests succeed
- ✅ Reference data is populated
- ✅ Monitoring system is functional

### Successful Ingestion When:
- ✅ Data is ingested without duplicates
- ✅ Monitoring shows progress and completion
- ✅ Data quality checks pass
- ✅ Cross-reference analysis works
- ✅ Error rates are minimal (<1%)

## 📞 Support

For issues with:
- **API Keys**: Check respective API documentation
- **Database**: Verify PostgreSQL connection and permissions
- **Monitoring**: Check monitoring setup in `monitoring/database_setup.md`
- **Deduplication**: Run `python scripts/analyze_members_deduplication.py --validate`

The ingestion system is now ready for production use with comprehensive monitoring and proper deduplication across all data sources!