#!/usr/bin/env python3
"""
Comprehensive GitHub Issue Creation for OpenDiscourse Ingestion Issues
Creates detailed GitHub issues for all identified ingestion problems
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any

class GitHubIssueCreator:
    def __init__(self, token: str, repo_owner: str, repo_name: str):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create a GitHub issue"""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"
        data = {
            "title": title,
            "body": body,
            "labels": labels or []
        }

        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Failed to create issue '{title}': {response.status_code} - {response.text}")
            return None

    def get_existing_issues(self) -> List[Dict[str, Any]]:
        """Get existing issues to avoid duplicates"""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"
        params = {"state": "open", "per_page": 100}

        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        return []

def create_ingestion_issues():
    """Create comprehensive GitHub issues for ingestion problems"""

    # Get GitHub token from environment
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN environment variable required")
        return

    creator = GitHubIssueCreator(token, "cbwinslow", "opendiscourse")

    # Check existing issues
    existing_issues = creator.get_existing_issues()
    existing_titles = {issue['title'].lower() for issue in existing_issues}
    print(f"📋 Found {len(existing_issues)} existing issues")

    # Define all ingestion issues
    issues = [
        {
            "title": "🚨 CRITICAL: Congress Bills Ingestion Complete Failure",
            "body": """## 🚨 **CRITICAL: Congress Bills Ingestion Complete Failure**

### **Problem Summary**
The Congress Bills ingestion system is completely non-functional - it processes 60,000+ records from the API but inserts **ZERO** records into the database.

### **Current Status**
- ✅ Congress Members: 725 records (working)
- ❌ Congress Bills: 0 records (COMPLETE FAILURE)
- ✅ OpenStates People: 1,752 records (working)

### **Root Cause Analysis**
1. **Chamber Mapping Foreign Key Constraint Violation**
   - API returns "House" but database expects "house" (lowercase)
   - Foreign key constraint fails during insertion
   - All bill records rejected during batch insert

2. **Data Transformation Logic Gap**
   - Missing chamber mapping in data normalization layer
   - No case conversion for API response values

### **Steps to Reproduce**
```bash
# 1. Test chamber mapping (fails)
python test_minimal.py  # Lines 104-120

# 2. Attempt bills ingestion (fails with FK constraint)
python scripts/ingest_congress_bills_incremental.py --congress 118

# 3. Check database result
psql -d opendiscourse -c "SELECT COUNT(*) FROM congress.bills;"  # Returns 0
```

### **Immediate Fix Required**
Add chamber mapping in data transformation:
```python
# In scripts/ingest_congress_bills_incremental.py
chamber_mapping = {
    'House': 'house',
    'Senate': 'senate',
    'Joint': 'joint'
}

# Apply mapping during data normalization
if bill_data.get('chamber') in chamber_mapping:
    bill_data['chamber'] = chamber_mapping[bill_data['chamber']]
```

### **Files Requiring Updates**
- `scripts/ingest_congress_bills_incremental.py` - Add chamber mapping
- `test_minimal.py:104-120` - Fix chamber mapping test
- Database schema: Verify `congress.chambers` table values

### **Business Impact**
- **HIGH**: Core legislative data completely missing
- **URGENT**: Blocks all Congress-related analysis
- **BLOCKING**: Prevents complete dataset creation

### **Estimated Fix Time**
2-4 hours for proper implementation and testing

### **Testing Requirements**
1. Unit test chamber mapping logic
2. Integration test with sample bill data
3. Full ingestion test with small congress (e.g., 118)
4. Verify foreign key constraints satisfied

### **Rollback Plan**
- Current system already non-functional
- Safe to implement fix without risk
- Backup existing data before changes

---
**Priority**: 🔴 Critical
**Assignee**: @cbwinslow
**Labels**: bug, ingestion, congress, priority-critical""",
            "labels": ["bug", "ingestion", "congress", "priority-critical"]
        },
        {
            "title": "Script Parameter Mismatches - Comprehensive Bulk Ingestion Failure",
            "body": """## Script Parameter Mismatches - Comprehensive Bulk Ingestion Failure

### **Problem Summary**
The comprehensive bulk ingestion script uses incorrect command parameters that don't exist, causing all 131 jobs to fail with exit code 2.

### **Current Status**
- ✅ Total Jobs Created: 131
- ❌ Jobs Completed: 0
- ❌ Jobs Failed: 131 (100% failure rate)
- 📊 Records Processed: 0

### **Root Cause Analysis**
1. **Congress Script Parameter Error**
   - Using `--data-type members` (doesn't exist)
   - Congress script only accepts: `--source`, `--congress`, `--bill-type`, `--limit`, `--data-dir`

2. **OpenStates Command Structure Error**
   - Using direct parameters like `--jurisdiction ca`
   - Should use subcommands: `ingest-people --jurisdiction ca`

3. **GovInfo Parameter Issues**
   - Similar parameter mismatches in GovInfo ingestion calls

### **Steps to Reproduce**
```bash
# 1. Run comprehensive ingestion (fails)
python scripts/comprehensive_bulk_ingestion.py

# 2. Check error logs
tail -f logs/comprehensive_bulk_ingestion.log
# Shows: "unrecognized arguments: --data-type members"

# 3. Check individual script help
python3 scripts/data_ingestion/congress_api_ingest.py --help
# Shows available parameters (no --data-type)
```

### **Immediate Fixes Required**

#### **1. Fix Congress Members Command**
```python
# WRONG (current):
command = [sys.executable, "scripts/data_ingestion/congress_api_ingest.py",
    "--source", "congress", "--congress", str(congress), "--data-type", "members"]

# CORRECT:
command = [sys.executable, "scripts/data_ingestion/congress_api_ingest.py",
    "--source", "congress", "--congress", str(congress)]
```

#### **2. Fix OpenStates Commands**
```python
# WRONG (current):
command = [sys.executable, "scripts/ingestion/openstates_cli.py",
    "--jurisdiction", jurisdiction, "--data-types", "people,bills"]

# CORRECT:
command = [sys.executable, "scripts/ingestion/openstates_cli.py",
    "ingest-people", "--jurisdiction", jurisdiction]
```

### **Files Requiring Updates**
- `scripts/comprehensive_bulk_ingestion.py` - Lines 158-163, 175-181, 235-240
- All command generation logic needs parameter fixes

### **Business Impact**
- **HIGH**: Complete bulk ingestion system non-functional
- **URGENT**: Blocks all data ingestion operations
- **BLOCKING**: Prevents dataset expansion

### **Estimated Fix Time**
1-2 hours to update all command parameters

### **Testing Requirements**
1. Test each individual script with correct parameters
2. Verify help output matches expected parameters
3. Run small test ingestion (1-2 jobs)
4. Full bulk ingestion test

### **Rollback Plan**
- Current system non-functional
- Parameter fixes are additive, no data risk
- Can revert to individual script execution if needed

---
**Priority**: 🔴 Critical
**Assignee**: @cbwinslow
**Labels**: bug, ingestion, parameters, priority-critical""",
            "labels": ["bug", "ingestion", "parameters", "priority-critical"]
        },
        {
            "title": "OpenStates Command Structure Issues - 60 Jobs Failing",
            "body": """## OpenStates Command Structure Issues - 60 Jobs Failing

### **Problem Summary**
All 60 OpenStates ingestion jobs are failing because the comprehensive script uses wrong CLI command structure.

### **Current Status**
- ✅ Congress Jobs: 71 (mostly working after parameter fixes)
- ❌ OpenStates Jobs: 60 (100% failure rate)
- ✅ GovInfo Jobs: 8 (working after parameter fixes)

### **Root Cause Analysis**
1. **Wrong Command Format**
   - Current: `python scripts/ingestion/openstates_cli.py --jurisdiction ca --data-types people,bills`
   - Should be: `python scripts/ingestion/openstates_cli.py ingest-people --jurisdiction ca`

2. **Subcommand Structure Ignored**
   - OpenStates CLI uses subcommands (ingest-people, ingest-bills, etc.)
   - Comprehensive script treats it like direct parameter script

### **Steps to Reproduce**
```bash
# 1. Check OpenStates CLI help (works)
source .env && source .venv/bin/activate
python3 scripts/ingestion/openstates_cli.py --help

# 2. Try wrong format (fails)
python3 scripts/ingestion/openstates_cli.py --jurisdiction ca
# Error: "unrecognized arguments: --jurisdiction"

# 3. Try correct format (works)
python3 scripts/ingestion/openstates_cli.py ingest-people --jurisdiction ca --dry-run
```

### **Correct Command Structures**
```bash
# People ingestion:
python3 scripts/ingestion/openstates_cli.py ingest-people --jurisdiction ca

# Bills ingestion:
python3 scripts/ingestion/openstates_cli.py ingest-bills --jurisdiction ca

# All data for jurisdiction:
python3 scripts/ingestion/openstates_cli.py ingest-all-states --jurisdiction ca

# Status check:
python3 scripts/ingestion/openstates_cli.py status
```

### **Immediate Fixes Required**
Update comprehensive ingestion script command generation:

```python
# WRONG (current):
job_id = f"openstates_people_{jurisdiction}"
command = [
    sys.executable, "scripts/ingestion/openstates_cli.py",
    "--jurisdiction", jurisdiction,
    "--data-types", "people"
]

# CORRECT:
job_id = f"openstates_people_{jurisdiction}"
command = [
    sys.executable, "scripts/ingestion/openstates_cli.py",
    "ingest-people",
    "--jurisdiction", jurisdiction
]
```

### **Files Requiring Updates**
- `scripts/comprehensive_bulk_ingestion.py` - OpenStates command generation section
- Lines around 200-250 (OpenStates job creation)

### **Business Impact**
- **MEDIUM**: 60 jobs failing but Congress/GovInfo working
- **URGENT**: Blocks state-level legislative data
- **SCOPE**: 30 states × 2 data types affected

### **Estimated Fix Time**
1 hour to update OpenStates command structures

### **Testing Requirements**
1. Test OpenStates CLI with correct subcommands
2. Verify dry-run mode works
3. Test small jurisdiction (CA) ingestion
4. Full OpenStates bulk ingestion test

### **Rollback Plan**
- Low risk - command structure changes only
- Can fall back to individual OpenStates script execution
- No data impact, only execution changes

---
**Priority**: 🟡 High
**Assignee**: @cbwinslow
**Labels**: bug, openstates, ingestion, priority-high""",
            "labels": ["bug", "openstates", "ingestion", "priority-high"]
        },
        {
            "title": "Database Connection Inconsistencies - Wrong Database Names",
            "body": """## Database Connection Inconsistencies - Wrong Database Names

### **Problem Summary**
Multiple scripts use incorrect database connection parameters that violate project standards and cause connection failures.

### **Project Standards (from agents.md)**
```python
# ✅ CORRECT (MUST USE)
conn = psycopg2.connect(
    database='opendiscourse',  # NEVER 'cbwinslow'
    user='cbwinslow',
    host='/var/run/postgresql'  # NEVER 'localhost'
)
```

### **Found Issues**
1. **Wrong Database Name**
   - Some scripts use `database='cbwinslow'` instead of `database='opendiscourse'`
   - Causes connection failures during ingestion

2. **Wrong Host Specification**
   - Some scripts use `host='localhost'` instead of Unix socket
   - Less reliable and may fail under load

3. **Inconsistent Connection Patterns**
   - Different connection strings across scripts
   - Maintenance nightmare and debugging difficulties

### **Affected Files Identified**
```bash
# Files with known issues:
scripts/enhanced_openstates_ingestion.py:530-533  # Wrong database name
scripts/ingestion/monitoring_delegates.py         # Check connection pattern
scripts/ingestion/bulk_ingest.py                  # Verify connection
```

### **Steps to Reproduce**
```bash
# 1. Check for wrong database connections
grep -r "database='cbwinslow'" scripts/
grep -r "host='localhost'" scripts/

# 2. Test connection with wrong parameters (fails)
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
    print('WRONG: This should fail')
except Exception as e:
    print(f'EXPECTED FAILURE: {e}')
"

# 3. Test correct connection (works)
python3 -c "
import psycopg2
conn = psycopg2.connect(database='opendiscourse', user='cbwinslow', host='/var/run/postgresql')
print('CORRECT: Connection successful')
"
```

### **Comprehensive Fix Required**
Audit and fix all database connections:

```python
# STANDARDIZED CONNECTION PATTERN (copy-paste ready)
import psycopg2

def get_database_connection():
    """Standard database connection following project standards"""
    return psycopg2.connect(
        database='opendiscourse',  # ALWAYS use 'opendiscourse'
        user='cbwinslow',           # ALWAYS use 'cbwinslow'
        host='/var/run/postgresql' # ALWAYS use Unix socket
    )
```

### **Files to Audit and Fix**
```bash
# High priority files:
scripts/enhanced_openstates_ingestion.py
scripts/ingestion/congress_api_ingest.py
scripts/ingestion/openstates_cli.py
scripts/comprehensive_bulk_ingestion.py

# Check all Python scripts:
find scripts/ -name "*.py" -exec grep -l "psycopg2.connect" {} \;
```

### **Business Impact**
- **MEDIUM**: Some scripts fail during execution
- **MAINTENANCE**: Inconsistent patterns cause debugging issues
- **STANDARDS**: Violates project database connection rules

### **Estimated Fix Time**
2-3 hours to audit and fix all connections

### **Testing Requirements**
1. Audit all database connections in codebase
2. Update to use standardized connection pattern
3. Test each updated script's database connectivity
4. Run small ingestion test for each source

### **Prevention Measures**
1. Create database connection utility function
2. Add linting rule to check database connection patterns
3. Update coding standards documentation
4. Add connection pattern to code review checklist

---
**Priority**: 🟡 High
**Assignee**: @cbwinslow
**Labels**: database, standards, code-quality, priority-high""",
            "labels": ["database", "standards", "code-quality", "priority-high"]
        },
        {
            "title": "Missing Table Protection - No Safeguards Against Data Destruction",
            "body": """## Missing Table Protection - No Safeguards Against Data Destruction

### **Problem Summary**
Current ingestion scripts lack safeguards against accidentally dropping or recreating tables that contain data, risking catastrophic data loss.

### **Current Risk Assessment**
- ❌ **No table existence checks** before CREATE/DROP operations
- ❌ **No data backup verification** before destructive operations
- ❌ **No confirmation prompts** for potentially destructive actions
- ❌ **No rollback mechanisms** for accidental data loss

### **Project Protection Rules (from agents.md)**
```bash
# 🚨 ABSOLUTELY FORBIDDEN - NEVER INCLUDE THESE:
DROP DATABASE
DELETE FROM table_name  # without WHERE clause
TRUNCATE TABLE table_name
systemctl restart postgresql

# ✅ SAFE PATTERNS - ALWAYS USE:
IF EXISTS checks before operations
Manual confirmation for destructive actions
Data backups before structural changes
```

### **High-Risk Operations Identified**
1. **Table Recreation Without Checks**
   ```sql
   -- DANGEROUS (current pattern in some scripts):
   DROP TABLE IF EXISTS congress.bills;
   CREATE TABLE congress.bills (...);

   -- SAFE (required pattern):
   -- Check if table has data before dropping
   DO $$
   BEGIN
     IF NOT EXISTS (SELECT 1 FROM congress.bills LIMIT 1) THEN
       DROP TABLE IF EXISTS congress.bills;
       CREATE TABLE congress.bills (...);
     ELSE
       RAISE NOTICE 'Table has data, skipping recreation';
     END IF;
   END $$;
   ```

2. **Bulk Delete Operations**
   ```sql
   -- DANGEROUS:
   DELETE FROM congress.members;

   -- SAFE:
   DELETE FROM congress.members WHERE updated_at < '2024-01-01';
   -- or better: Use specific WHERE clauses
   ```

### **Steps to Reproduce Risk**
```bash
# 1. Search for dangerous patterns
grep -r "DROP TABLE" scripts/
grep -r "TRUNCATE TABLE" scripts/
grep -r "DELETE FROM.*WHERE.*1.*=.*1" scripts/

# 2. Check current table data status
psql -d opendiscourse -c "
SELECT schemaname, tablename, n_live_tup as rows
FROM pg_stat_user_tables
WHERE schemaname IN ('congress', 'openstates', 'govinfo')
ORDER BY schemaname, tablename;
"
```

### **Protection Mechanisms Required**

#### **1. Table Data Protection Function**
```python
def safe_table_operation(table_name: str, operation: str) -> bool:
    """Check if table has data before allowing destructive operations"""
    query = "SELECT EXISTS (SELECT 1 FROM %s LIMIT 1)" % table_name
    result = execute_query(query)

    if result and result[0]['exists']:
        print(f"⚠️  WARNING: Table {table_name} contains data")
        response = input(f"Proceed with {operation} on {table_name}? (yes/no): ")
        return response.lower() == 'yes'
    return True
```

#### **2. Automated Safety Checks**
```python
def validate_ingestion_safety(source: str, data_type: str) -> bool:
    """Pre-ingestion safety validation"""
    checks = [
        check_table_exists,
        check_table_has_data,
        check_backup_available,
        check_user_confirmation
    ]

    for check in checks:
        if not check(source, data_type):
            return False
    return True
```

### **Files Requiring Protection Updates**
```bash
# High priority - add safety checks:
scripts/data_ingestion/congress_api_ingest.py
scripts/ingestion/openstates_cli.py
scripts/comprehensive_bulk_ingestion.py

# Check all ingestion scripts:
find scripts/ -name "*ingest*.py" -exec grep -l "DROP\|TRUNCATE\|DELETE.*FROM" {} \;
```

### **Business Impact**
- **CRITICAL**: Risk of catastrophic data loss
- **COMPLIANCE**: Violates project data protection rules
- **REPUTATION**: Single mistake could destroy months of work

### **Estimated Fix Time**
4-6 hours to implement comprehensive protection

### **Testing Requirements**
1. Test protection mechanisms with empty tables
2. Test protection mechanisms with populated tables
3. Verify user confirmation prompts work
4. Test rollback and backup procedures

### **Prevention Checklist**
- [ ] Add data existence checks before all DROP operations
- [ ] Implement user confirmation for destructive actions
- [ ] Create automated backup before structural changes
- [ ] Add audit logging for all destructive operations
- [ ] Implement read-only mode for production deployments

---
**Priority**: 🔴 Critical
**Assignee**: @cbwinslow
**Labels**: security, data-protection, database, priority-critical""",
            "labels": ["security", "data-protection", "database", "priority-critical"]
        },
        {
            "title": "API Rate Limiting Issues - Missing Rate Limit Protection",
            "body": """## API Rate Limiting Issues - Missing Rate Limit Protection

### **Problem Summary**
Several ingestion scripts lack proper API rate limiting, causing failed requests, IP bans, and unreliable ingestion.

### **Current Rate Limit Status**
- ✅ **Congress.gov**: Has rate limiting (2 req/sec)
- ❌ **OpenStates**: Missing rate limiting in some scripts
- ❌ **GovInfo**: Inconsistent rate limiting implementation
- ❌ **Comprehensive Script**: No coordinated rate limiting across sources

### **API Rate Limits (Official)**
```bash
# Congress.gov API:
- 120 requests/minute (2 req/sec)
- Strict enforcement with 429 responses

# OpenStates API:
- 100 requests/minute (1.67 req/sec)
- Daily quotas apply

# GovInfo.gov API:
- 100 requests/minute (1.67 req/sec)
- Collection-specific limits may apply
```

### **Issues Identified**

#### **1. OpenStates Scripts Missing Rate Limits**
```python
# DANGEROUS (current pattern in some scripts):
for jurisdiction in jurisdictions:
    response = requests.get(f"https://api.openstates.org/v3/jurisdictions/{jurisdiction}")
    # No rate limiting between requests!
```

#### **2. No Coordinated Rate Limiting**
```python
# PROBLEM: Multiple sources running simultaneously
# Congress: 2 req/sec
# OpenStates: 1.67 req/sec
# GovInfo: 1.67 req/sec
# TOTAL: 5.34 req/sec - May hit combined limits
```

#### **3. No Exponential Backoff**
```python
# MISSING: Proper retry logic with backoff
try:
    response = requests.get(url)
except requests.exceptions.RequestException:
    # Current: Immediate failure
    # Needed: Exponential backoff retry
```

### **Steps to Reproduce Issues**
```bash
# 1. Run ingestion without rate limiting (may work initially)
python scripts/ingest_openstates_people.py

# 2. Monitor for rate limit errors
tail -f logs/ingestion.log | grep "429\|rate limit\|too many requests"

# 3. Check IP ban status
curl -I "https://api.openstates.org/v3/jurisdictions"
# Check for 429 or 403 responses
```

### **Comprehensive Rate Limiting Solution**

#### **1. Unified Rate Limiter Class**
```python
import time
import threading
from collections import deque
from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    requests_per_second: float
    burst_capacity: int = 10

class UnifiedRateLimiter:
    def __init__(self):
        self.limits = {
            'congress': RateLimitConfig(2.0, 10),
            'openstates': RateLimitConfig(1.67, 8),
            'govinfo': RateLimitConfig(1.67, 8)
        }
        self.request_times = {source: deque() for source in self.limits}
        self.locks = {source: threading.Lock() for source in self.limits}

    def wait_if_needed(self, source: str):
        """Wait if rate limit would be exceeded"""
        config = self.limits[source]
        now = time.time()

        with self.locks[source]:
            times = self.request_times[source]

            # Remove old requests outside time window
            window_start = now - (config.burst_capacity / config.requests_per_second)
            while times and times[0] < window_start:
                times.popleft()

            # Check if we'd exceed rate limit
            if len(times) >= config.burst_capacity:
                sleep_time = (1.0 / config.requests_per_second) - (now - times[-1])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            times.append(now)
```

#### **2. Rate-Limited Request Wrapper**
```python
def rate_limited_request(source: str, url: str, max_retries: int = 3):
    """Make API request with rate limiting and retry logic"""
    rate_limiter = UnifiedRateLimiter()

    for attempt in range(max_retries):
        try:
            rate_limiter.wait_if_needed(source)
            response = requests.get(url, timeout=30)

            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 5))
                time.sleep(retry_after * (2 ** attempt))  # Exponential backoff
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

    raise Exception(f"Failed after {max_retries} attempts")
```

### **Files Requiring Updates**
```bash
# Add rate limiting to:
scripts/ingestion/openstates_cli.py
scripts/data_ingestion/congress_api_ingest.py
scripts/comprehensive_bulk_ingestion.py

# Check all API calling scripts:
find scripts/ -name "*.py" -exec grep -l "requests\.get\|requests\.post" {} \;
```

### **Business Impact**
- **MEDIUM**: Intermittent ingestion failures
- **RELIABILITY**: Unpredictable success rates
- **REPUTATION**: API providers may block abusive requests

### **Estimated Fix Time**
3-4 hours to implement comprehensive rate limiting

### **Testing Requirements**
1. Test rate limiting with various request patterns
2. Verify exponential backoff works correctly
3. Test coordinated rate limiting across sources
4. Monitor API response headers for rate limit info

### **Monitoring Requirements**
```python
# Add rate limit monitoring:
- Track requests per second per source
- Monitor 429 response frequency
- Alert on rate limit threshold breaches
- Log retry attempts and backoff periods
```

---
**Priority**: 🟡 High
**Assignee**: @cbwinslow
**Labels**: api, rate-limiting, reliability, priority-high""",
            "labels": ["api", "rate-limiting", "reliability", "priority-high"]
        }
    ]

    # Create issues
    created_issues = []
    for issue in issues:
        if issue['title'].lower() not in existing_titles:
            print(f"📝 Creating issue: {issue['title']}")
            result = creator.create_issue(issue['title'], issue['body'], issue['labels'])
            if result:
                created_issues.append(result)
                print(f"✅ Created issue #{result['number']}")
            else:
                print(f"❌ Failed to create issue")
        else:
            print(f"⏭️  Issue already exists: {issue['title']}")

    print(f"\n🎉 Created {len(created_issues)} new issues")
    print("📊 Summary:")
    for issue in created_issues:
        print(f"   - #{issue['number']}: {issue['title']}")

    return created_issues

if __name__ == "__main__":
    print("🚀 Creating GitHub Issues for OpenDiscourse Ingestion Problems")
    print("=" * 60)
    create_ingestion_issues()
