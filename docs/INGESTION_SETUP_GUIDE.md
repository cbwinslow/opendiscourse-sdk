# Congress Members Ingestion - Complete Setup Guide

## 🎯 Overview

This guide provides a complete setup for automated Congress members data ingestion, including comprehensive testing, monitoring, and scheduling capabilities.

## 📁 Project Structure

```
opendiscourse/
├── scripts/
│   ├── ingest_members_official.py      # Main ingestion script
│   ├── verify_congress_data.py         # Data verification utility
│   ├── ingestion_scheduler.py          # Automated scheduler
│   ├── setup_ingestion.sh              # Setup script
│   ├── populate_sessions.py            # Reference data
│   └── populate_reference_tables.py   # Reference data
├── tests/
│   ├── test_congress_data_patterns.py  # Data pattern tests
│   └── test_ingestion_integration.py   # Integration tests
├── migrations/
│   ├── 004_member_verification_views.sql
│   ├── 005_member_verification_procedures.sql
│   └── 006_member_verification_functions.sql
├── config/
│   └── ingestion_config.json           # Configuration file
├── logs/                               # Ingestion logs
├── backups/                            # Database backups
└── docs/
    ├── VERIFICATION_QUERIES_REFERENCE.md
    └── CONGRESS_MEMBERS_INGESTION_COMPLETE.md
```

## 🚀 Quick Start

### 1. Run Setup Script

```bash
# Navigate to project directory
cd /home/cbwinslow/Videos/opendiscourse

# Run the setup script
./scripts/setup_ingestion.sh
```

The setup script will:
- ✅ Create necessary directories
- ✅ Make scripts executable
- ✅ Check environment variables
- ✅ Test database and API connectivity
- ✅ Run database migrations
- ✅ Populate reference data
- ✅ Run initial tests
- ✅ Set up scheduling instructions

### 2. Manual Setup (Alternative)

```bash
# Create directories
mkdir -p logs backups config

# Make scripts executable
chmod +x scripts/*.py

# Set environment variables
export CONGRESS_API_KEY=your_api_key_here
export DB_NAME=cbwinslow
export DB_USER=cbwinslow

# Run database migrations
psql -U cbwinslow -d cbwinslow -f migrations/004_member_verification_views.sql
psql -U cbwinslow -d cbwinslow -f migrations/005_member_verification_procedures.sql
psql -U cbwinslow -d cbwinslow -f migrations/006_member_verification_functions.sql

# Populate reference data (if needed)
python scripts/populate_sessions.py
python scripts/populate_reference_tables.py
```

## 📊 Usage

### Basic Ingestion

```bash
# Run full ingestion (Congress 101-118)
python scripts/ingestion_scheduler.py

# Run specific congress range
python scripts/ingestion_scheduler.py --congress-start 118 --congress-end 118

# Run with custom batch size
python scripts/ingestion_scheduler.py --batch-size 20
```

### Data Verification

```bash
# Run verification only
python scripts/ingestion_scheduler.py --verify-only

# Detailed verification
python scripts/verify_congress_data.py

# Congress-specific verification
python scripts/verify_congress_data.py --summary 118

# Member career analysis
python scripts/verify_congress_data.py --bioguide S001207
```

### Database Operations

```bash
# Create backup
python scripts/ingestion_scheduler.py --backup-only

# Check data quality
python scripts/verify_congress_data.py --check-quality

# Clean duplicates
python scripts/verify_congress_data.py --clean-duplicates
```

## 🧪 Testing

### Run All Tests

```bash
# Data pattern tests
python -m pytest tests/test_congress_data_patterns.py -v

# Integration tests
python -m pytest tests/test_ingestion_integration.py -v

# All tests
python -m pytest tests/ -v
```

### Specific Test Categories

```bash
# Test data integrity
python -m pytest tests/test_congress_data_patterns.py::TestCongressDataPatterns -v

# Test data anomalies
python -m pytest tests/test_congress_data_patterns.py::TestCongressDataAnomalies -v

# Test ingestion integration
python -m pytest tests/test_ingestion_integration.py::TestIngestionIntegration -v
```

## ⏰ Automated Scheduling

### Set Up Cron Job

```bash
# Get cron setup instructions
python scripts/ingestion_scheduler.py --setup-cron

# Example output:
# crontab -e
# Add this line:
# 0 2 * * 0 /path/to/python /path/to/ingestion_scheduler.py --auto >> /path/to/logs/cron_ingestion.log 2>&1
```

### Manual Cron Setup

```bash
# Edit crontab
crontab -e

# Add for weekly Sunday 2 AM ingestion
0 2 * * 0 cd /home/cbwinslow/Videos/opendiscourse && python scripts/ingestion_scheduler.py --auto >> logs/cron_ingestion.log 2>&1

# Add for daily verification
0 6 * * * cd /home/cbwinslow/Videos/opendiscourse && python scripts/verify_congress_data.py >> logs/daily_verification.log 2>&1
```

## ⚙️ Configuration

### Edit Configuration

```bash
# Edit configuration file
nano config/ingestion_config.json
```

### Configuration Options

```json
{
  "ingestion": {
    "congress_start": 101,        # Starting congress
    "congress_end": 118,          # Ending congress
    "batch_size": 50,             # API batch size
    "request_delay": 0.5,         # Delay between requests
    "max_retries": 3              # Maximum retry attempts
  },
  "schedule": {
    "enabled": false,             # Enable scheduled ingestion
    "frequency": "weekly",         # weekly, daily, monthly
    "day_of_week": "sunday",      # Day for weekly schedule
    "time": "02:00",              # Time of day
    "timezone": "UTC"             # Timezone
  },
  "verification": {
    "enabled": true,              # Enable verification
    "run_after_ingestion": true,  # Run verification after ingestion
    "data_quality_threshold": 0.95 # Quality threshold
  },
  "notifications": {
    "enabled": false,             # Enable notifications
    "email": null,                # Email address
    "webhook_url": null           # Webhook URL
  },
  "backup": {
    "enabled": true,              # Enable backups
    "backup_before_ingestion": true,
    "backup_retention_days": 30   # Days to keep backups
  }
}
```

## 📈 Monitoring

### Log Files

```bash
# View ingestion logs
tail -f logs/ingestion.log

# View cron logs
tail -f logs/cron_ingestion.log

# View verification logs
tail -f logs/verify_congress_data.log
```

### Database Monitoring

```sql
-- Quick data overview
SELECT 
    (SELECT COUNT(*) FROM congress.members) as unique_members,
    (SELECT COUNT(*) FROM congress.member_terms) as total_terms,
    (SELECT COUNT(DISTINCT congress_number) FROM congress.member_terms) as congresses;

-- Recent ingestion activity
SELECT * FROM congress.member_counts_by_congress ORDER BY congress_number DESC;

-- Data quality check
CALL congress.check_data_quality();
```

### Performance Monitoring

```bash
# Check query performance
python scripts/verify_congress_data.py --stats

# Monitor database size
psql -U cbwinslow -d cbwinslow -c "
    SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
    FROM pg_tables 
    WHERE schemaname = 'congress'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. API Key Issues
```bash
# Check API key
curl -H "X-API-Key: $CONGRESS_API_KEY" "https://api.congress.gov/v3/member/congress/118?limit=1"

# Reset API key
export CONGRESS_API_KEY=your_new_api_key
```

#### 2. Database Connection Issues
```bash
# Test database connection
psql -U cbwinslow -d cbwinslow -c "SELECT 1;"

# Check database status
psql -U cbwinslow -d cbwinslow -c "\dt congress.*"
```

#### 3. Permission Issues
```bash
# Fix script permissions
chmod +x scripts/*.py

# Fix directory permissions
chmod 755 logs backups config
```

#### 4. Data Quality Issues
```bash
# Run data quality check
python scripts/verify_congress_data.py --check-quality

# Clean duplicates
python scripts/verify_congress_data.py --clean-duplicates

# Re-ingest problematic data
python scripts/ingestion_scheduler.py --congress-start 118 --congress-end 118
```

### Error Recovery

```bash
# Restore from backup (if needed)
psql -U cbwinslow -d cbwinslow -f backups/congress_backup_YYYYMMDD_HHMMSS.sql

# Re-run reference data setup
python scripts/populate_sessions.py
python scripts/populate_reference_tables.py

# Re-run migrations
psql -U cbwinslow -d cbwinslow -f migrations/004_member_verification_views.sql
psql -U cbwinslow -d cbwinslow -f migrations/005_member_verification_procedures.sql
psql -U cbwinslow -d cbwinslow -f migrations/006_member_verification_functions.sql
```

## 📚 Reference Documentation

- **[Verification Queries Reference](docs/VERIFICATION_QUERIES_REFERENCE.md)** - Complete SQL reference
- **[Ingestion Summary](docs/CONGRESS_MEMBERS_INGESTION_COMPLETE.md)** - Implementation details
- **[Data Patterns Test Suite](tests/test_congress_data_patterns.py)** - Comprehensive test cases
- **[Integration Tests](tests/test_ingestion_integration.py)** - End-to-end testing

## 🎯 Best Practices

### 1. Regular Monitoring
- Check logs daily
- Run verification weekly
- Monitor database size
- Track API usage

### 2. Data Quality
- Run quality checks after each ingestion
- Monitor for anomalies
- Keep backups before major changes
- Document any data issues

### 3. Performance
- Use appropriate batch sizes
- Monitor API rate limits
- Optimize database queries
- Clean up old logs and backups

### 4. Security
- Rotate API keys regularly
- Use environment variables for secrets
- Limit database permissions
- Monitor access logs

## 🚀 Next Steps

1. **Set up automated scheduling** using cron
2. **Configure notifications** for ingestion results
3. **Set up monitoring dashboards** for data quality
4. **Integrate with other OpenDiscourse modules**
5. **Set up automated testing** in CI/CD pipeline

The ingestion system is now fully operational with comprehensive testing, monitoring, and automation capabilities!