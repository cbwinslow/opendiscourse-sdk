# OpenDiscourse AI Agents Configuration

## 🤖 Agent Mandates for API Key Enforcement

### Core Agent Directives

**MANDATORY REQUIREMENT: API Keys Must Be Used For Every Single API Call - NO EXCEPTIONS**

All AI agents working on this project must follow these immutable rules:

1. **API Key Enforcement**: Every API call to congress.gov, govinfo.gov, and openstates.org MUST use real API keys from environment variables
2. **No Demo Keys**: Demo/placeholder keys are NEVER permitted under any circumstances
3. **Environment Variables**: All API keys must be sourced from .env file using python-dotenv
4. **Validation Required**: API keys must be validated before any ingestion process begins
5. **Fail Fast**: Scripts must terminate immediately if required API keys are missing or invalid

### Agent Responsibilities

#### 📋 Data Ingestion Agent
- **Primary Role**: Execute bulk data ingestion with mandatory API key validation
- **Required Actions**:
  - Always call `validate_all_api_keys()` before starting ingestion
  - Use production mode for all real data ingestion
  - Verify API key presence and validity for all three services
  - Implement proper error handling for API authentication failures
  - Log API key status without exposing actual key values
  - **CRITICAL**: Verify database connection parameters before starting ingestion
  - **CRITICAL**: Use correct database name (`opendiscourse`, not `cbwinslow`)
  - **CRITICAL**: Use Unix socket path (`/var/run/postgresql`) for reliable connections

#### 🔍 API Validation Agent
- **Primary Role**: Ensure all API keys are valid and functional
- **Required Actions**:
  - Test each API key with actual API calls before ingestion
  - Validate API key format and detect demo/placeholder keys
  - Check rate limits and quota status
  - Provide detailed validation reports
  - Maintain API key health monitoring

#### 🛡️ Security Enforcement Agent
- **Primary Role**: Enforce security policies for API key usage
- **Required Actions**:
  - Prevent hardcoded API keys in source code
  - Ensure environment variable isolation
  - Validate API key scope and permissions
  - Audit API key usage patterns
  - Report any security violations immediately

#### 📊 Monitoring Agent
- **Primary Role**: Monitor ingestion processes and API usage
- **Required Actions**:
  - Track API quota usage during bulk operations
  - Monitor rate limiting and implement backoff strategies
  - Log ingestion progress with API key status
  - Alert on API authentication failures
  - Maintain comprehensive audit trails

#### 🔧 Database Debugging Agent
- **Primary Role**: Diagnose and fix database ingestion issues
- **Required Actions**:
  - Verify database schema matches script expectations
  - Check function parameter signatures before calling
  - Validate table structures and column names
  - Monitor actual database inserts vs processed records
  - Debug checkpoint function mismatches
  - Ensure proper error handling for database operations

### Agent Workflow Requirements

#### Pre-Ingestion Validation (MANDATORY)
```python
# REQUIRED AGENT WORKFLOW - NO EXCEPTIONS
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env

# 1. Validate all API keys
key_validation = validate_all_api_keys()
if not key_validation['valid']:
    raise ValueError("API key validation failed - cannot proceed")

# 2. Get production mode
mode = get_ingestion_mode_from_env()
if mode.value != 'production':
    raise ValueError("Only production mode allowed for real data ingestion")

# 3. Verify database connection
import psycopg2
try:
    conn = psycopg2.connect(
        database='opendiscourse',
        user='cbwinslow',
        host='/var/run/postgresql'
    )
    conn.close()
except Exception as e:
    raise ValueError(f"Database connection failed: {e}")

# 4. Proceed with ingestion
# ... ingestion code
```

#### Database Connection Standards (MANDATORY)
```python
# REQUIRED DATABASE CONNECTION PATTERN - NO EXCEPTIONS
import psycopg2

# CORRECT database connection
conn = psycopg2.connect(
    database='opendiscourse',  # NOT 'cbwinslow'
    user='cbwinslow',
    host='/var/run/postgresql'  # Unix socket for reliability
)

# FORBIDDEN patterns
conn = psycopg2.connect(database='cbwinslow')  # WRONG DATABASE
conn = psycopg2.connect()  # MISSING PARAMETERS
```

#### API Call Standards (MANDATORY)
```python
# REQUIRED API CALL PATTERN - NO EXCEPTIONS
from dotenv import load_dotenv
load_dotenv()

import os
import requests

# Get API key from environment
api_key = os.getenv('REQUIRED_API_KEY')
if not api_key:
    raise ValueError("API key environment variable is required")

# Validate API key is not a demo key
demo_patterns = ['DEMO_KEY', 'TEST_KEY', 'PLACEHOLDER', 'YOUR_API_KEY']
if any(pattern in api_key.upper() for pattern in demo_patterns):
    raise ValueError("Demo/placeholder keys not allowed")

# Make API call with proper headers
headers = {
    'X-API-Key': api_key,
    'Accept': 'application/json'
}
response = requests.get(url, headers=headers)
```

### Agent Error Handling Requirements

#### Mandatory Error Scenarios
1. **Missing API Key**: Immediate termination with clear error message
2. **Invalid API Key**: Immediate termination with validation details
3. **Demo Key Detection**: Immediate termination with security violation notice
4. **API Rate Limiting**: Implement exponential backoff, never proceed without valid API
5. **Authentication Failure**: Log error and terminate, never use fallback keys
6. **Database Connection Failure**: Immediate termination with connection details
7. **Function Parameter Mismatch**: Log exact function signature and fix parameters
8. **Schema Mismatch**: Verify table structure before data insertion

#### Error Response Templates
```python
# REQUIRED ERROR RESPONSES - NO EXCEPTIONS
if not api_key:
    raise ValueError(f"{api_key_name} environment variable is required - cannot proceed with ingestion")

if 'DEMO' in api_key.upper():
    raise ValueError(f"Demo key detected in {api_key_name} - real API key required for production ingestion")

if response.status_code == 401:
    raise ValueError(f"API authentication failed for {service} - check {api_key_name} environment variable")

# Database connection errors
if 'database' in str(e).lower():
    raise ValueError(f"Database connection failed - check database name and connection parameters")
```

### Agent Compliance Monitoring

#### Automated Compliance Checks
- ✅ All scripts must import and use `ingestion_config.validate_all_api_keys()`
- ✅ All API calls must use environment variables, never hardcoded keys
- ✅ All ingestion must run in production mode for real data
- ✅ All error handling must terminate on API key failures
- ✅ All logging must not expose actual API key values
- ✅ All database connections must use correct database name and socket path
- ✅ All function calls must match actual function signatures

#### Violation Reporting
Any agent that detects API key violations must:
1. Immediately terminate the process
2. Log the violation with details
3. Report to security enforcement agent
4. Prevent any data access until compliance is restored

### Agent Success Criteria

#### Mandatory Success Metrics
- **API Key Validation**: 100% success rate before any ingestion
- **Real Key Usage**: 0% tolerance for demo/placeholder keys
- **Environment Compliance**: 100% usage of environment variables
- **Error Handling**: 100% termination on API key failures
- **Database Connections**: 100% successful connections with correct parameters
- **Data Insertion**: Actual database records must match processed records
- **Function Calls**: 100% correct parameter matching

#### Performance Requirements
- **Validation Speed**: API key validation must complete within 5 seconds
- **Error Response**: Must terminate within 1 second of detecting invalid keys
- **Monitoring**: Real-time API quota and rate limit tracking
- **Compliance**: 100% adherence to all API key enforcement rules

---

## 🔒 SECURITY MANDATE

**THIS DOCUMENT CONTAINS MANDATORY SECURITY REQUIREMENTS**

**VIOLATION OF THESE RULES CONSTITUTES A SECURITY BREACH**

**ALL AGENTS MUST COMPLY - NO EXCEPTIONS**

**API KEYS MUST BE USED FOR EVERY SINGLE API CALL - ALWAYS**

## 🚨 CRITICAL DATABASE PROTECTION RULES

### AUTOMATIC SERVICE RESTARTS - ABSOLUTELY FORBIDDEN
- ❌ **NEVER** generate code with `systemctl restart postgresql`
- ❌ **NEVER** generate code with `systemctl reload postgresql`
- ❌ **NEVER** generate code with `service postgres restart`
- ❌ **NEVER** create automated setup scripts that restart services
- ❌ **NEVER** modify PostgreSQL configuration without manual approval

### DATABASE DESTRUCTION COMMANDS - ABSOLUTELY FORBIDDEN
- ❌ **NEVER** generate `DROP DATABASE` commands
- ❌ **NEVER** generate `DELETE FROM` without WHERE clause
- ❌ **NEVER** generate `TRUNCATE TABLE` in production code
- ❌ **NEVER** create scripts that can wipe data automatically

### SAFE DATABASE OPERATIONS ONLY
- ✅ Always require manual confirmation for database changes
- ✅ Always create backups before structural changes
- ✅ Use migration files for schema changes
- ✅ Include proper error handling and rollback procedures
- ✅ Always check if databases/tables exist before creating or dropping them

---

## 🔧 Git Operations and Security Agent

### Primary Role
Manage version control operations while enforcing security policies and handling GitHub secret scanning compliance.

### Required Actions for Git Operations

#### 🔑 PAT (Personal Access Token) Management
```bash
# REQUIRED PAT Configuration Pattern
git remote set-url origin https://username:PAT_TOKEN@github.com/owner/repository.git

# Example with proper PAT integration
GITHUB_PAT="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"
git remote set-url origin https://cbwinslow:${GITHUB_PAT}@github.com/cbwinslow/opendiscourse.git
```

#### 🚨 GitHub Secret Scanning Response
When GitHub blocks pushes due to secret scanning:
1. **Immediate Action**: Identify the problematic commit and files
2. **Assessment**: Determine if secrets are in current code or commit history
3. **Resolution Options**:
   - Use GitHub's secret unblock URLs for authorized secrets
   - Remove secrets from commit history using `git filter-branch` or BFG
   - Create clean branch from commit before secrets were introduced
   - Rewrite history to permanently remove sensitive data

#### 📋 Secret Scanning Troubleshooting
```bash
# Check repository status
git status
git remote -v

# Identify problematic commits
git log --oneline -10
git show --name-only COMMIT_HASH

# Check for tracked secret files
git ls-files | grep -E "(\.env|\.key|password|token)"
```

#### 🔄 Branch Management for Security Issues
```bash
# Create clean branch from pre-secret commit
git checkout -b clean-push-$(date +%Y%m%d-%H%M) COMMIT_BEFORE_SECRETS

# Remove problematic files from history
git rm --cached sensitive-file.conf
git commit -m "Remove sensitive files from repository tracking"

# Push with force if needed (after cleanup)
git push origin --force-with-lease branch-name
```

### Git Security Enforcement Rules

#### ❌ FORBIDDEN Git Practices
- Never commit actual API keys, passwords, or tokens
- Never push branches with secrets in commit history
- Never use force push without understanding implications
- Never ignore GitHub secret scanning warnings
- Never bypass security blocks without proper authorization

#### ✅ REQUIRED Git Practices
- Always use environment variables for sensitive data
- Always check `.gitignore` before committing
- Always verify remote URL includes proper authentication
- Always commit `.gitignore` updates to prevent future secret leaks
- Always use PAT tokens for automation (never passwords)

#### 🛡️ Pre-Push Security Checklist
```bash
# MANDATORY PRE-PUSH VALIDATION
1. ✅ Check git status for unexpected changes
2. ✅ Verify .gitignore includes sensitive file patterns
3. ✅ Scan for potential secrets in modified files
4. ✅ Test push to feature branch before main branch
5. ✅ Ensure PAT token has appropriate repository permissions
6. ✅ Review commit messages for sensitive information
```

### Secret Scanning Resolution Procedures

#### Option 1: GitHub Unblock (Fastest)
```bash
# Visit GitHub-provided unblock URLs
# Example URLs from error messages:
# https://github.com/owner/repo/security/secret-scanning/unblock-secret/TOKEN_ID
# Follow GitHub's web interface to authorize specific secrets
```

#### Option 2: History Cleanup (Most Secure)
```bash
# Remove specific files from entire Git history
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch path/to/sensitive-file' \
--prune-empty --tag-name-filter cat -- --all

# Push cleaned history
git push origin --force --all
```

#### Option 3: Clean Branch Creation (Recommended)
```bash
# Create new branch from clean commit
git checkout -b new-clean-branch CLEAN_COMMIT_HASH

# Cherry-pick only safe commits
git cherry-pick SAFE_COMMIT_HASH

# Push clean branch
git push origin new-clean-branch
```

### Error Handling for Git Operations

#### Common Git Push Errors and Solutions
```bash
# GH013: Repository rule violations
# Solution: Follow secret scanning resolution procedures above

# Authentication errors
# Solution: Verify PAT token validity and permissions

# Merge conflicts
# Solution: Use proper merge strategies, never force push blindly

# Large file errors
# Solution: Use Git LFS or remove large files from history
```

### Agent Compliance Monitoring for Git

#### Automated Git Security Checks
- ✅ All pushes must pass secret scanning
- ✅ All commits must use PAT authentication
- ✅ All branches must have clean history before main branch merge
- ✅ All `.gitignore` patterns must prevent sensitive file commits
- ✅ All repository URLs must use secure authentication methods

#### Violation Response
Any agent detecting Git security violations must:
1. Immediately halt push operations
2. Report the specific security issue
3. Provide resolution steps
4. Prevent further operations until compliance is restored

---

## 🔒 SECURITY MANDATE

---

## 📊 CURRENT INGESTION STATUS

### ✅ WORKING INGESTION SYSTEMS
- **Congress Members**: 725 records ✅ (Congresses 116, 117, 118)
- **OpenStates People**: 1,040 records ✅ (CA, TX, NY, FL, IL, OH)
- **OpenStates Jurisdictions**: 59 records ✅
- **Congress Bills**: Ingestion functions implemented & verified (dry-run) ✅
  - `ingest-bills`
  - `ingest-bill-actions`
  - `ingest-bill-cosponsors`
  - `ingest-bill-subjects`
  - `ingest-bill-titles`
  - `ingest-related-bills`

### ⚠️ PARTIALLY WORKING SYSTEMS
- **OpenStates**:
  - `ingest-organizations`: Implemented but blocked by jurisdiction resolution bug
  - `ingest-sessions`: Implemented but blocked by jurisdiction resolution bug
  - `ingest-documents`: Implemented but blocked by jurisdiction resolution bug

### ❌ BROKEN INGESTION SYSTEMS
- **OpenStates Jurisdiction Resolution**: `resolve_jurisdiction_id('ca')` fails to resolve

### 🔧 KNOWN SOLUTIONS
1. **Database Connection**: Use `database='opendiscourse'` and `host='/var/run/postgresql'`
2. **Function Parameters**: Match exact function signatures (8 parameters for `update_checkpoint_progress`)
3. **Schema Validation**: Verify table structures before data insertion
4. **Error Handling**: Check actual database inserts vs processed records

---

## 🎯 AGENT DEBUGGING PROCEDURES

### When Ingestion Fails:
1. **Check Database Connection**: Verify correct database name and socket path
2. **Verify Function Signatures**: Use `\df function_name` to check parameters
3. **Monitor Actual Inserts**: Compare processed records vs database counts
4. **Check Checkpoints**: Review `incremental.ingestion_checkpoints` for real progress
5. **Validate Schema**: Ensure table columns match script expectations

### Required Debugging Queries:
```sql
-- Check actual database records
SELECT count(*) FROM target_table;

-- Check checkpoint progress
SELECT * FROM incremental.ingestion_checkpoints
WHERE data_source = 'source' AND data_type = 'type';

-- Verify function signatures
\df schema.function_name;

-- Check table structure
\d schema.table_name;
```

---

## 🔒 SECURITY MANDATE

**THIS DOCUMENT CONTAINS MANDATORY SECURITY REQUIREMENTS**

**VIOLATION OF THESE RULES CONSTITUTES A SECURITY BREACH**

**ALL AGENTS MUST COMPLY - NO EXCEPTIONS**

**API KEYS MUST BE USED FOR EVERY SINGLE API CALL - ALWAYS**

## 🚨 CRITICAL DATABASE OPERATIONS MANDATE

**NON-DESTRUCTIVE OPERATIONS ONLY:**

- ✅ **ALWAYS** check if a database or table already exists before attempting to create or drop it.
- ❌ **NEVER** proceed with `CREATE DATABASE`, `CREATE TABLE`, `DROP DATABASE`, or `DROP TABLE` if the target already exists, unless explicitly confirmed by the user after a clear warning.
- ✅ Ensure all database manipulation scripts are idempotent where possible, meaning they can be run multiple times without causing unintended side effects (e.g., using `CREATE TABLE IF NOT EXISTS`).
- ✅ Prioritize `ALTER TABLE` for schema modifications over dropping and recreating tables.
