# OpenDiscourse Data Ingestion Procedures

## 🎯 **OVERVIEW**

This document outlines the complete data ingestion procedures for the OpenDiscourse legislative database, including current status, known issues, solutions, and step-by-step processes.

---

## 📊 **CURRENT INGESTION STATUS**

### ✅ **WORKING INGESTION SYSTEMS**
- **Congress Members**: 725 records ✅ (Congresses 116, 117, 118)
  - **Script**: `scripts/ingest_congress_members_incremental.py`
  - **Performance**: 15-42 records/second
  - **Status**: Fully operational

- **OpenStates People**: 1,040 records ✅ (CA: 121, TX: 182, NY: 214, FL: 161, IL: 178, OH: 134)
  - **Script**: `scripts/ingest_openstates_people.py`
  - **Performance**: 300-2700 records/second
  - **Status**: Fully operational

- **OpenStates Jurisdictions**: 59 records ✅
  - **Script**: `simple_jurisdictions_ingest.py`
  - **Performance**: Fast completion
  - **Status**: Fully operational

### ❌ **BROKEN INGESTION SYSTEMS**
- **Congress Bills**: 0 records ❌ (Processes 60,000+ but inserts 0)
  - **Script**: `scripts/ingest_congress_bills_incremental.py`
  - **Issue**: Data insertion logic broken, not duplicate detection
  - **Status**: Script runs but no database records created

---

## 🚨 **CRITICAL ISSUES & SOLUTIONS**

### **Issue 1: Congress Bills Ingestion Failure**
**Problem**: Script processes bills but inserts 0 records into database

**Root Causes Identified**:
1. **Database Connection**: Wrong database name (`cbwinslow` instead of `opendiscourse`)
2. **Function Parameter Mismatch**: `update_checkpoint_progress` called with wrong parameters
3. **Data Normalization Issues**: Bill data not properly normalized for insertion

**Solutions Applied**:
```python
# 1. Fixed database connection
conn = psycopg2.connect(
    database='opendiscourse',  # CORRECT
    user='cbwinslow',
    host='/var/run/postgresql'  # Unix socket
)

# 2. Fixed function call (8 parameters required)
cursor.execute("""
    SELECT incremental.update_checkpoint_progress(
        'congress.gov', 'bills', %s, %s, NULL, NULL, NULL, NULL, %s
    )
""", (str(congress), offset, batch_size))

# 3. Fixed error_summary column name
UPDATE incremental.ingestion_sessions SET error_summary = %s  # NOT error_message
```

**Current Status**: Still broken - data insertion logic needs further debugging

---

## 🔧 **DATABASE CONNECTION STANDARDS**

### **MANDATORY CONNECTION PATTERN**
```python
import psycopg2

# CORRECT - Always use this pattern
conn = psycopg2.connect(
    database='opendiscourse',  # MUST be 'opendiscourse'
    user='cbwinslow',
    host='/var/run/postgresql'  # MUST use Unix socket
)

# FORBIDDEN PATTERNS
conn = psycopg2.connect(database='cbwinslow')  # WRONG DATABASE
conn = psycopg2.connect()  # MISSING PARAMETERS
conn = psycopg2.connect(host='localhost')  # WRONG HOST
```

### **Connection Validation**
```python
# Always validate connection before ingestion
try:
    conn = psycopg2.connect(
        database='opendiscourse',
        user='cbwinslow',
        host='/var/run/postgresql'
    )
    # Test connection
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    cursor.close()
except Exception as e:
    raise ValueError(f"Database connection failed: {e}")
```

---

## 📋 **INGESTION PROCEDURES**

### **Procedure 1: OpenStates People Ingestion (WORKING)**

#### **Step 1: Add Jurisdiction**
```sql
INSERT INTO openstates.jurisdictions (jurisdiction_id, name, classification, state_code)
VALUES ('ocd-jurisdiction/country:us/state:XX/government', 'StateName', 'state', 'xx')
ON CONFLICT (jurisdiction_id) DO NOTHING;
```

#### **Step 2: Run Ingestion**
```bash
python scripts/ingest_openstates_people.py --jurisdiction <state_code>
```

#### **Expected Results**
- **Performance**: 300-2700 records/second
- **Success Rate**: 100%
- **Error Handling**: Automatic retry with rate limiting

#### **Available States**
- ✅ California (ca) - 121 records
- ✅ Texas (tx) - 182 records
- ✅ New York (ny) - 214 records
- ✅ Florida (fl) - 161 records
- ✅ Illinois (il) - 178 records
- ✅ Ohio (oh) - 134 records
- 📋 Pennsylvania (pa) - Ready (rate limited)
- 📋 More states available

---

### **Procedure 2: Congress Members Ingestion (WORKING)**

#### **Step 1: Run Ingestion**
```bash
python scripts/ingest_congress_members_incremental.py --congress <number>
```

#### **Expected Results**
- **Performance**: 15-42 records/second
- **Success Rate**: 100%
- **Available Congresses**: 116, 117, 118

---

### **Procedure 3: Congress Bills Ingestion (BROKEN)**

#### **Current Status**: NOT WORKING
#### **Issue**: Processes bills but inserts 0 records
#### **Debugging Steps**:
1. Check database connection parameters
2. Verify function signatures
3. Monitor actual inserts vs processed records
4. Check checkpoint progress

#### **Debugging Queries**:
```sql
-- Check actual records
SELECT count(*) FROM congress.bills;

-- Check checkpoint progress
SELECT * FROM incremental.ingestion_checkpoints
WHERE data_source = 'congress.gov' AND data_type = 'bills';

-- Verify function signature
\df incremental.update_checkpoint_progress;

-- Check table structure
\d congress.bills;
```

---

## 🛡️ **ERROR HANDING & DEBUGGING**

### **Mandatory Pre-Ingestion Validation**
```python
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env
import psycopg2

# 1. Validate API keys
key_validation = validate_all_api_keys()
if not key_validation['valid']:
    raise ValueError("API key validation failed - cannot proceed")

# 2. Verify production mode
mode = get_ingestion_mode_from_env()
if mode.value != 'production':
    raise ValueError("Only production mode allowed for real data ingestion")

# 3. Test database connection
try:
    conn = psycopg2.connect(
        database='opendiscourse',
        user='cbwinslow',
        host='/var/run/postgresql'
    )
    conn.close()
except Exception as e:
    raise ValueError(f"Database connection failed: {e}")
```

### **Debugging Checklist**
When ingestion fails, follow these steps IN ORDER:

1. **Check Database Connection**
   ```bash
   psql -d opendiscourse -c "SELECT 1;"
   ```

2. **Verify Function Signatures**
   ```bash
   psql -d opendiscourse -c "\df incremental.update_checkpoint_progress"
   ```

3. **Check Actual Data**
   ```bash
   psql -d opendiscourse -c "SELECT count(*) FROM target_table;"
   ```

4. **Review Checkpoints**
   ```bash
   psql -d opendiscourse -c "SELECT * FROM incremental.ingestion_checkpoints WHERE data_source = 'source' AND data_type = 'type';"
   ```

5. **Validate Schema**
   ```bash
   psql -d opendiscourse -c "\d schema.table_name;"
   ```

---

## 📈 **PERFORMANCE METRICS**

### **Working Systems Performance**
| Data Source | Records/sec | Success Rate | Status |
|-------------|-------------|--------------|---------|
| OpenStates People | 300-2700 | 100% | ✅ WORKING |
| Congress Members | 15-42 | 100% | ✅ WORKING |
| Jurisdictions | Fast | 100% | ✅ WORKING |
| Congress Bills | 0 | 0% | ❌ BROKEN |

### **Database Size**
- **Total Database**: 13MB
- **Records Ingested**: 1,824 total
- **Backup Size**: 632KB compressed

---

## 🔄 **BACKUP PROCEDURES**

### **Automated Backup Script**
```bash
# Run backup
./simple_backup.sh

# Manual backup commands
pg_dump -h /var/run/postgresql -U cbwinslow -d opendiscourse \
  --schema=congress --schema=openstates --schema=incremental \
  --no-owner --no-privileges -f backup_$(date +%Y%m%d_%H%M%S).sql
```

### **Backup Verification**
```bash
# Check backup file size
ls -lh backup_*.sql

# Test restore (to backup database)
psql -h /var/run/postgresql -U cbwinslow -d backup_db -f backup_file.sql
```

---

## 🎯 **NEXT STEPS & PRIORITIES**

### **High Priority**
1. **Fix Congress Bills Ingestion**
   - Debug data insertion logic
   - Verify bill data normalization
   - Test with small batches first

2. **Expand OpenStates Coverage**
   - Add remaining states (PA, NJ, GA, etc.)
   - Handle rate limiting properly
   - Target 2,000+ total state legislators

### **Medium Priority**
3. **Add Member Terms Data**
   - Complete congress member information
   - Add chamber assignments and terms

4. **Start Bills Ingestion for Other Sources**
   - OpenStates bills
   - GovInfo bills

### **Low Priority**
5. **Performance Optimization**
   - Improve batch processing
   - Optimize database queries
   - Add parallel processing

---

## 📞 **TROUBLESHOOTING CONTACT**

### **When Issues Occur**
1. **Check this document first** for known solutions
2. **Run debugging checklist** in order
3. **Review error logs** for specific error messages
4. **Check database connection** before anything else

### **Common Error Solutions**
- **API Key Issues**: Check .env file, validate keys aren't demo keys
- **Database Connection**: Use `opendiscourse` database, Unix socket
- **Function Errors**: Verify parameter counts match function signatures
- **Rate Limiting**: Wait for reset, implement backoff

---

## 📝 **CHANGE LOG**

### **2025-11-26**
- Added comprehensive database connection standards
- Documented Congress bills ingestion issues
- Added debugging procedures and checklists
- Updated performance metrics and status
- Added backup procedures

### **2025-11-25**
- Initial ingestion procedures documentation
- Added working OpenStates and Congress members procedures
- Documented API key enforcement requirements

---

*This document is maintained as part of the OpenDiscourse project. Update when new issues are discovered or solutions are implemented.*
