# Bulk Data Ingestion Procedure

## 🔒 MANDATORY REQUIREMENTS - NO EXCEPTIONS

### **CRITICAL SECURITY MANDATE**
**EVERY API CALL MUST USE REAL API KEYS FROM ENVIRONMENT VARIABLES**
**DEMO/PLACEHOLDER KEYS ARE ABSOLUTELY FORBIDDEN**
**VALIDATION IS REQUIRED BEFORE EVERY INGESTION PROCESS**

---

## 📋 Pre-Ingestion Checklist (MANDATORY)

### ✅ **Step 1: Environment Variable Verification**
```bash
# REQUIRED: Verify all environment variables are set
echo "CONGRESS_API_KEY: $CONGRESS_API_KEY"
echo "GOVINFO_API_KEY: $GOVINFO_API_KEY"
echo "OPENSTATES_API_KEY: $OPENSTATES_API_KEY"
echo "INGESTION_MODE: $INGESTION_MODE"
```

**Requirements:**
- All three API keys must be present
- INGESTION_MODE must be set to "production"
- No demo/placeholder keys allowed
- Keys must be real, valid API keys

### ✅ **Step 2: API Key Validation**
```python
# REQUIRED: Run validation before any ingestion
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env

# Validate all API keys
key_validation = validate_all_api_keys()
if not key_validation['valid']:
    print("❌ API KEY VALIDATION FAILED")
    for error in key_validation['errors']:
        print(f"   🚫 {error}")
    raise ValueError("Cannot proceed with ingestion - API keys invalid")

# Verify production mode
mode = get_ingestion_mode_from_env()
if mode.value != 'production':
    raise ValueError("Only production mode allowed for bulk ingestion")

print("✅ API keys validated - proceeding with ingestion")
```

### ✅ **Step 3: Database Connection Test**
```python
# REQUIRED: Verify database connectivity
import psycopg2
try:
    conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    cursor.close()
    conn.close()
    print("✅ Database connection verified")
except Exception as e:
    raise ValueError(f"Database connection failed: {e}")
```

---

## 🚀 Bulk Ingestion Execution

### **Method 1: Incremental Ingestion (Recommended)**
```bash
# REQUIRED: Use production mode with real API keys
INGESTION_MODE=production python scripts/ingest_congress_incremental.py
```

**Features:**
- Resume capability for interrupted processes
- Checkpoint tracking for progress monitoring
- Fingerprinting for duplicate detection
- Real-time progress reporting

### **Method 2: Monitored Ingestion**
```bash
# REQUIRED: Use production mode with monitoring
INGESTION_MODE=production python scripts/ingest_members_monitored.py --disable-monitoring
```

**Features:**
- Enhanced progress monitoring
- Session tracking
- Detailed error reporting
- Configurable batch sizes

### **Method 3: Specific Congress Range**
```bash
# REQUIRED: Specify congress range for targeted ingestion
INGESTION_MODE=production python -c "
from scripts.ingest_congress_incremental import IncrementalCongressIngestor
ingestor = IncrementalCongressIngestor()
results = ingestor.ingest_all_congresses(116, 118)
print(f'Ingestion complete: {results}')
"
```

---

## 📊 Monitoring and Verification

### **Real-time Progress Monitoring**
```python
# REQUIRED: Monitor ingestion progress
import psycopg2
conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
cursor = conn.cursor()

# Check checkpoint status
cursor.execute("""
    SELECT category, total_processed, total_estimated, completion_percentage, is_completed
    FROM incremental.checkpoint_status
    WHERE data_source = 'congress.gov' AND data_type = 'members'
    ORDER BY category
""")

checkpoints = cursor.fetchall()
for cp in checkpoints:
    congress, processed, estimated, percentage, completed = cp
    status = "✅ COMPLETE" if completed else "🔄 IN PROGRESS"
    print(f"Congress {congress}: {processed}/{estimated} ({percentage:.1f}%) - {status}")

cursor.close()
conn.close()
```

### **API Usage Monitoring**
```python
# REQUIRED: Track API quota and rate limits
from ingestion_config import APIKeyValidator
validator = APIKeyValidator()

# Check rate limit status for each API
congress_status = validator.check_rate_limit_status(
    os.getenv('CONGRESS_API_KEY'),
    "https://api.congress.gov/v3"
)

govinfo_status = validator.check_rate_limit_status(
    os.getenv('GOVINFO_API_KEY'),
    "https://api.govinfo.gov"
)

openstates_status = validator.check_rate_limit_status(
    os.getenv('OPENSTATES_API_KEY'),
    "https://v3.openstates.org"
)

print(f"Congress.gov Rate Limit: {congress_status}")
print(f"GovInfo.gov Rate Limit: {govinfo_status}")
print(f"OpenStates Rate Limit: {openstates_status}")
```

---

## 🛑 Error Handling Procedures

### **API Key Failures**
```python
# REQUIRED: Immediate termination on API key issues
if not api_key:
    raise ValueError("API key environment variable is required - cannot proceed")

if 'DEMO' in api_key.upper() or 'PLACEHOLDER' in api_key.upper():
    raise ValueError("DEMO/PLACEHOLDER KEY DETECTED - SECURITY VIOLATION")

if response.status_code == 401:
    raise ValueError("API AUTHENTICATION FAILED - CHECK API KEY")
```

### **Rate Limiting**
```python
# REQUIRED: Exponential backoff for rate limiting
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10))
def api_call_with_retry(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 429:
        raise Exception("Rate limited - retrying")
    response.raise_for_status()
    return response
```

### **Database Failures**
```python
# REQUIRED: Transaction rollback on database errors
try:
    # Database operations
    cursor.execute("INSERT INTO congress.members ...")
    conn.commit()
except Exception as e:
    conn.rollback()
    raise ValueError(f"Database operation failed: {e}")
```

---

## 📈 Post-Ingestion Verification

### **Data Integrity Checks**
```python
# REQUIRED: Verify data integrity after ingestion
import psycopg2
conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
cursor = conn.cursor()

# Check total records
cursor.execute("SELECT COUNT(*) FROM congress.members")
total_count = cursor.fetchone()[0]
print(f"Total members in database: {total_count:,}")

# Check for duplicates
cursor.execute("""
    SELECT bioguide_id, COUNT(*)
    FROM congress.members
    GROUP BY bioguide_id
    HAVING COUNT(*) > 1
""")
duplicates = cursor.fetchall()
if duplicates:
    print(f"❌ DUPLICATES FOUND: {len(duplicates)}")
    for dup in duplicates:
        print(f"  {dup[0]}: {dup[1]} records")
else:
    print("✅ NO DUPLICATES FOUND")

cursor.close()
conn.close()
```

### **Checkpoint Verification**
```python
# REQUIRED: Verify all checkpoints are complete
cursor.execute("""
    SELECT category, total_processed, total_estimated, is_completed
    FROM incremental.ingestion_checkpoints
    WHERE data_source = 'congress.gov' AND data_type = 'members'
""")

checkpoints = cursor.fetchall()
all_complete = True
for cp in checkpoints:
    congress, processed, estimated, completed = cp
    if not completed:
        print(f"❌ Congress {congress} incomplete: {processed}/{estimated}")
        all_complete = False

if all_complete:
    print("✅ ALL CONGRESSES COMPLETE")
else:
    print("❌ SOME CONGRESSES INCOMPLETE")
```

---

## 🔒 Security Compliance

### **MANDATORY Security Checks**
- ✅ All API keys from environment variables only
- ✅ No hardcoded keys in source code
- ✅ Demo/placeholder key detection and rejection
- ✅ Production mode enforcement
- ✅ Audit trail logging

### **Prohibited Actions**
- ❌ Using demo keys in any environment
- ❌ Hardcoding API keys in scripts
- ❌ Skipping API key validation
- ❌ Using fallback keys on failures
- ❌ Exposing API keys in logs or outputs

---

## 📋 Standard Operating Procedure

### **Daily Bulk Ingestion**
1. **Preparation**: Verify environment variables
2. **Validation**: Run `validate_all_api_keys()`
3. **Execution**: Run ingestion in production mode
4. **Monitoring**: Track progress and API usage
5. **Verification**: Check data integrity and completion
6. **Logging**: Record session details and any issues

### **Recovery Procedures**
1. **Interruption**: Resume from last checkpoint
2. **API Failure**: Check key validity and rate limits
3. **Database Issue**: Verify connectivity and permissions
4. **Data Corruption**: Restore from last known good state

---

## 🎯 SUCCESS CRITERIA

### **Required Outcomes**
- ✅ 100% API key validation success
- ✅ All congresses at 100% completion
- ✅ Zero duplicate records
- ✅ Complete audit trail
- ✅ No security violations

### **Performance Targets**
- ✅ API response time < 2 seconds
- ✅ Batch processing 50 records/batch
- ✅ Error recovery < 5 seconds
- ✅ Validation completion < 10 seconds

---

## 🚨 EMERGENCY PROCEDURES

### **API Key Compromise**
1. **Immediate**: Stop all ingestion processes
2. **Security**: Report to security team
3. **Rotation**: Replace compromised API keys
4. **Audit**: Review all recent API usage
5. **Recovery**: Resume with new keys after validation

### **System Failure**
1. **Assessment**: Identify failure point
2. **Isolation**: Prevent further data corruption
3. **Recovery**: Restore from last good checkpoint
4. **Verification**: Test system integrity
5. **Monitoring**: Enhanced monitoring during recovery

---

## 📞 SUPPORT CONTACTS

### **Technical Issues**
- **API Problems**: Check API key validity and rate limits
- **Database Issues**: Verify connectivity and permissions
- **System Errors**: Review logs and error messages

### **Security Issues**
- **API Key Problems**: Immediate security team notification
- **Unauthorized Access**: Security incident response
- **Data Breach**: Emergency security procedures

---

**THIS DOCUMENT CONTAINS MANDATORY OPERATIONAL PROCEDURES**

**VIOLATION OF THESE PROCEDURES CONSTITUTES A SECURITY BREACH**

**ALL API KEY REQUIREMENTS ARE MANDATORY - NO EXCEPTIONS**
