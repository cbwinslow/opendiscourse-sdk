# Bulk Data Ingestion Guide

## 🎯 Overview

This guide covers comprehensive bulk data ingestion for congressional bills and votes from multiple sources including Congress.gov, GovInfo, and OpenStates.

## 📁 Ingestion Scripts

### **Bills Ingestion**
- **Script**: `scripts/ingestion/bulk_bills_ingestion.py`
- **Sources**: Congress.gov, GovInfo, OpenStates
- **Features**: Multi-source ingestion, deduplication, batch processing

### **Votes Ingestion**
- **Script**: `scripts/ingestion/bulk_votes_ingestion.py`
- **Sources**: Congress.gov, GovInfo (Congressional Record)
- **Features**: Roll call votes, vote positions, member information

## 🚀 Quick Start

### **1. Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

### **2. Required Environment Variables**
```bash
DATABASE_URL=postgresql://user:password@localhost/opendiscourse
CONGRESS_API_KEY=your_congress_gov_api_key
GOVINFO_API_KEY=your_govinfo_api_key
OPENSTATES_API_KEY=your_openstates_api_key
```

### **3. Install Dependencies**
```bash
pip install psycopg2-binary requests python-dotenv pandas
```

## 📋 Usage Examples

### **Bills Ingestion**

#### **Ingest from All Sources**
```bash
python scripts/ingestion/bulk_bills_ingestion.py
```

#### **Ingest Specific Congress**
```bash
python scripts/ingestion/bulk_bills_ingestion.py --congress 118
```

#### **Ingest from Specific Sources**
```bash
python scripts/ingestion/bulk_bills_ingestion.py --sources congress govinfo
```

#### **Limit Number of Bills**
```bash
python scripts/ingestion/bulk_bills_ingestion.py --congress-limit 1000 --govinfo-limit 500
```

#### **Specific State from OpenStates**
```bash
python scripts/ingestion/bulk_bills_ingestion.py --openstates-state ca --openstates-limit 2000
```

### **Votes Ingestion**

#### **Ingest All Votes**
```bash
python scripts/ingestion/bulk_votes_ingestion.py
```

#### **Specific Congress and Chamber**
```bash
python scripts/ingestion/bulk_votes_ingestion.py --congress 118 --chamber house
```

#### **Both Chambers**
```bash
python scripts/ingestion/bulk_votes_ingestion.py --congress 118 --chamber both
```

#### **Limit Votes**
```bash
python scripts/ingestion/bulk_votes_ingestion.py --congress-limit 500
```

## 🗄️ Database Schema

### **Bills Tables**
```sql
-- Main bills table
CREATE TABLE congress.bills_bulk (
    bill_id VARCHAR(50) PRIMARY KEY,
    congress_number INTEGER,
    bill_type VARCHAR(10),
    bill_number INTEGER,
    official_title TEXT,
    short_title TEXT,
    introduced_date DATE,
    updated_date TIMESTAMP,
    sponsor_bioguide_id VARCHAR(20),
    sponsor_party VARCHAR(20),
    sponsor_state VARCHAR(10),
    committee_code VARCHAR(20),
    policy_area VARCHAR(100),
    subjects TEXT[],
    summary TEXT,
    latest_action TEXT,
    latest_action_date DATE,
    status VARCHAR(50),
    source VARCHAR(20),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### **Votes Tables**
```sql
-- Roll call votes
CREATE TABLE congress.roll_call_votes_bulk (
    vote_id VARCHAR(50) PRIMARY KEY,
    congress_number INTEGER,
    session INTEGER,
    chamber VARCHAR(20),
    roll_call_number INTEGER,
    vote_date DATE,
    vote_time TIME,
    vote_question TEXT,
    vote_description TEXT,
    vote_type VARCHAR(50),
    vote_result VARCHAR(50),
    yeas INTEGER,
    nays INTEGER,
    present INTEGER,
    not_voting INTEGER,
    democratic_position VARCHAR(20),
    republican_position VARCHAR(20),
    bill_id VARCHAR(50),
    amendment_number VARCHAR(20),
    nomination_number VARCHAR(20),
    source VARCHAR(20),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vote positions
CREATE TABLE congress.vote_positions_bulk (
    id SERIAL PRIMARY KEY,
    vote_id VARCHAR(50),
    member_bioguide_id VARCHAR(20),
    member_name VARCHAR(200),
    member_party VARCHAR(20),
    member_state VARCHAR(10),
    vote_position VARCHAR(20),
    vote_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (vote_id) REFERENCES congress.roll_call_votes_bulk(vote_id)
);
```

## 📊 Data Sources

### **Congress.gov API**
- **Bills**: Complete legislative information
- **Votes**: Roll call votes with positions
- **Rate Limit**: 10 requests/second
- **Authentication**: API key required

### **GovInfo API**
- **Bills**: Official legislative documents
- **Votes**: Congressional Record (limited vote data)
- **Rate Limit**: 1000 requests/hour
- **Authentication**: API key required

### **OpenStates API**
- **Bills**: State legislation (configurable by state)
- **Rate Limit**: 100 requests/minute
- **Authentication**: API key required

## ⚙️ Configuration

### **Batch Processing**
```python
# Default batch sizes
BATCH_SIZE = 100  # Number of records per batch
MAX_RETRIES = 3    # Number of retry attempts
RETRY_DELAY = 1.0  # Delay between retries
TIMEOUT = 30       # Request timeout in seconds
```

### **Source Priorities**
```python
# Default ingestion sources
DEFAULT_SOURCES = ['congress', 'govinfo', 'openstates']

# Source-specific settings
CONGRESS_LIMIT = 250    # Max records per API call
GOVINFO_LIMIT = 100     # Max records per API call
OPENSTATES_LIMIT = 50    # Max records per API call
```

## 📈 Monitoring and Tracking

### **Ingestion Statistics**
```sql
-- Bills ingestion tracking
SELECT * FROM congress.ingestion_tracking 
WHERE ingestion_type = 'bulk_ingestion' 
ORDER BY created_at DESC;

-- Votes ingestion tracking
SELECT * FROM congress.votes_ingestion_tracking 
ORDER BY created_at DESC;
```

### **Data Quality Checks**
```sql
-- Check for duplicates
SELECT bill_id, COUNT(*) as count
FROM congress.bills_bulk
GROUP BY bill_id
HAVING COUNT(*) > 1;

-- Check missing sponsor information
SELECT COUNT(*) as missing_sponsors
FROM congress.bills_bulk
WHERE sponsor_bioguide_id IS NULL;

-- Check vote position completeness
SELECT 
    vote_id,
    COUNT(*) as total_positions,
    COUNT(CASE WHEN member_bioguide_id IS NOT NULL THEN 1 END) as with_member_id
FROM congress.vote_positions_bulk
GROUP BY vote_id;
```

## 🔧 Advanced Features

### **Incremental Ingestion**
```bash
# Ingest only new/updated bills
python scripts/ingestion/bulk_bills_ingestion.py --incremental --since 2024-01-01

# Ingest recent votes
python scripts/ingestion/bulk_votes_ingestion.py --incremental --days 30
```

### **Custom Filtering**
```bash
# Filter by bill type
python scripts/ingestion/bulk_bills_ingestion.py --bill-types HR S HRES

# Filter by date range
python scripts/ingestion/bulk_votes_ingestion.py --start-date 2024-01-01 --end-date 2024-12-31
```

### **Parallel Processing**
```bash
# Run multiple sources in parallel
python scripts/ingestion/bulk_bills_ingestion.py --parallel --workers 4
```

## 🚨 Error Handling

### **Common Issues**
1. **API Rate Limits**: Automatic retry with exponential backoff
2. **Database Connection**: Connection pooling and retry logic
3. **Data Validation**: Schema validation before insertion
4. **Memory Usage**: Batch processing to prevent memory issues

### **Logging**
```bash
# View ingestion logs
tail -f bills_ingestion.log
tail -f votes_ingestion.log

# Error-only logs
grep ERROR bills_ingestion.log
```

## 📋 Best Practices

### **1. API Management**
- Monitor API usage and rate limits
- Use appropriate batch sizes
- Implement caching where possible
- Handle API errors gracefully

### **2. Database Performance**
- Use appropriate indexes
- Batch insert operations
- Monitor database connections
- Regular maintenance and vacuuming

### **3. Data Quality**
- Validate data before insertion
- Handle missing or incomplete data
- Implement deduplication logic
- Regular data quality checks

### **4. Monitoring**
- Track ingestion statistics
- Monitor error rates
- Set up alerts for failures
- Regular performance reviews

## 🔄 Maintenance

### **Regular Tasks**
```bash
# Update existing records
python scripts/ingestion/bulk_bills_ingestion.py --update-existing

# Clean up old data
python scripts/ingestion/cleanup_old_data.py --days 365

# Reconcile data sources
python scripts/ingestion/reconcile_sources.py
```

### **Performance Optimization**
```sql
-- Rebuild indexes
REINDEX TABLE congress.bills_bulk;
REINDEX TABLE congress.roll_call_votes_bulk;

-- Update statistics
ANALYZE congress.bills_bulk;
ANALYZE congress.roll_call_votes_bulk;
```

## 📚 Related Documentation

- [Political Analysis Guide](../analysis/POLITICAL_ANALYSIS_GUIDE.md)
- [Database Schema](../database/SCHEMA_CONSOLIDATION.md)
- [API Documentation](../api/API_REFERENCE.md)
- [Deployment Guide](../deployment/DEPLOYMENT_INSTRUCTIONS.md)

---

**Status**: ✅ **Production Ready** - Comprehensive bulk ingestion system for bills and votes with multi-source support and robust error handling.