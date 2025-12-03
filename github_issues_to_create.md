# GitHub Issues to Create for OpenDiscourse Project

Based on comprehensive code analysis, here are the GitHub issues that should be created:

## Critical Issues (High Priority)

### 1. Congress Bills Ingestion - Foreign Key Constraint Violation
**Title**: Congress Bills ingestion fails due to chamber mapping foreign key constraint violation
**Body**:
The Congress Bills ingestion is currently failing with foreign key constraint violations related to chamber mapping. The API returns "House" but the database expects "house" (lowercase).

**Current Status**:
- Congress Members: 725 records (working ✅)
- Congress Bills: 0 records (failing ❌)
- OpenStates People: 1,752 records (working ✅)

**Steps to Reproduce**:
1. Run `python test_minimal.py` - Chamber mapping test fails
2. Attempt Congress Bills ingestion - Foreign key constraint violation

**Expected Fix**:
Implement proper chamber mapping in the data transformation layer:
```python
chamber_mapping = {
    'House': 'house',
    'Senate': 'senate',
    'Joint': 'joint'
}
```

**Affected Files**:
- `test_minimal.py:104-120` (chamber mapping test)
- `scripts/ingest_congress_bills_incremental.py` (ingestion script)
- Database schema: `congress.chambers` table

**Labels**: bug, ingestion, congress, priority-high

---

### 2. Enhanced OpenStates Ingestion - Missing Implementation
**Title**: Enhanced OpenStates ingestion has placeholder methods that need implementation
**Body**:
The `scripts/enhanced_openstates_ingestion.py` file contains sophisticated infrastructure for parallel processing, rate limiting, and data validation, but several core ingestion methods are not implemented (just placeholders).

**Missing Implementations**:
- `ingest_person_details()` - Person details enrichment
- `ingest_person_bill_relationships()` - Person-bill relationships
- `ingest_bills_with_details()` - Bills ingestion (currently TODO)
- `ingest_committees_with_details()` - Committees ingestion (currently TODO)
- `ingest_events_with_details()` - Events ingestion (currently TODO)

**Current Status**:
- Basic people ingestion: ✅ Working
- Enhanced data types: ❌ Not implemented

**Expected Fix**:
Implement the placeholder methods in `scripts/enhanced_openstates_ingestion.py` lines 819-842.

**Labels**: enhancement, openstates, ingestion, priority-high

---

## Medium Priority Issues

### 3. Monitoring System Issues
**Title**: Multiple monitoring system issues identified requiring fixes
**Body**:
The monitoring system has several documented issues that need attention:

**Issue 3a**: Delegate Registration Mismatch for Congress Member Terms
- `monitoring/delegates.py:72-85` vs `scripts/ingest_members_monitored.py:345-366`
- Inconsistent progress tracking for term data

**Issue 3b**: Missing Error Recovery Mechanism
- No retry logic for failed database insertions
- Batch rollback loses all data instead of quarantining failed records

**Issue 3c**: Progress Percentage Calculation Flaw
- Can show progress > 100% when total_estimated is None

**Issue 3d**: Missing Monitoring for GovInfo Delegates
- Delegate registered but not integrated with actual workflows

**Affected Files**:
- `monitoring/delegates.py`
- `monitoring/progress_monitor.py`
- `scripts/ingest_members_monitored.py`

**Labels**: monitoring, bug, database, priority-medium

---

### 4. Data Validation and Processing Issues
**Title**: Several data validation and processing improvements needed
**Body**:

**Issue 4a**: Hardcoded State Mapping
- State name to code mapping is hardcoded in `scripts/ingest_members_monitored.py:213-228`
- Should be database-driven for maintainability

**Issue 4b**: Redundant Date Parsing Logic
- In `scripts/ingest_members_monitored.py:270-282` both if/else branches perform identical parsing
- Copy-paste error needs fixing

**Issue 4c**: Throughput Calculation Edge Case
- Uses arbitrary 0.01 minute minimum in `monitoring/progress_monitor.py:175`
- Could skew initial throughput calculations

**Labels**: maintainability, data-processing, priority-medium

---

### 5. Documentation and Standards Issues
**Title**: Inconsistent database connection parameters across codebase
**Body**:
Found multiple instances of incorrect database connection patterns that don't follow the project's standards.

**Current Standards** (from `agents.md`):
```python
# ✅ CORRECT
conn = psycopg2.connect(
    database='opendiscourse',  # NEVER 'cbwinslow'
    user='cbwinslow',
    host='/var/run/postgresql'  # NEVER 'localhost'
)
```

**Found Issues**:
- `scripts/enhanced_openstates_ingestion.py:530-533` uses wrong database name 'cbwinslow'
- Multiple files may have similar issues

**Required Fix**:
Audit all database connections to ensure they follow the correct patterns specified in `agents.md`.

**Labels**: database, standards, code-quality, priority-medium

---

## Enhancement Issues (Project v2 Related)

### 6. Vector Database Integration
**Title**: Complete PGVector integration for documentation search
**Body**:
The project has RAG setup documentation but needs full PGVector integration for semantic search across ingested documents.

**Current Status**:
- RAG setup documented in `docs/rag/RAG_SETUP.md`
- PGVector mentioned in requirements
- Integration not complete

**Required Work**:
1. Complete PGVector setup and configuration
2. Implement document embedding pipeline
3. Create semantic search endpoints
4. Add vector similarity queries

**Labels**: enhancement, vector-database, rag, project-v2

---

### 7. Congress API Enhancement
**Title**: Expand Congress data ingestion to include historical data
**Body**:
Currently ingesting Congresses 116, 117, 118. Expand to include historical Congress data and additional data types.

**Current Coverage**:
- Congress Members: 725 records ✅
- Congress Bills: 0 records (broken) ❌

**Enhancement Goals**:
1. Fix current bills ingestion
2. Add historical Congress data (115 and earlier)
3. Add roll call votes
4. Add committee data
5. Add amendment data

**Labels**: enhancement, congress, historical-data, project-v2

---

### 8. OpenStates Scraper Improvements
**Title**: OpenStates scrapers have many TODO comments that need addressing
**Body**:
Found 144 TODO/FIXME/BUG comments across the OpenStates scrapers that need addressing.

**Major Categories**:
- Session date updates (multiple jurisdictions need date corrections)
- Vote processing improvements
- Committee data enhancements
- Error handling improvements
- API integration fixes

**Priority Areas**:
- `openstates-scrapers/scrapers/nh/bills.py:405` - Fake vote passing logic
- `openstates-scrapers/scrapers/nc/bills.py:205` - Vote scraper needs fixing
- Multiple scrapers have session date TODO comments

**Labels**: openstates, scrapers, cleanup, project-v2

---

## Automation and Infrastructure Issues

### 9. GitHub Integration Automation
**Title**: Enhance existing GitHub sync automation for better issue management
**Body**:
The project has a GitHub sync setup (`scripts/github_sync_setup.py`) that creates labels and milestones, but could be enhanced to automatically create issues from monitoring system logs.

**Current Capabilities**:
- Labels and milestones setup ✅
- Agent log parsing script exists ✅
- Issue templates configured ✅

**Enhancement Goals**:
1. Automate monitoring issue creation
2. Add issue templates for common patterns
3. Implement issue linking and referencing
4. Add milestone tracking for ingestion progress

**Labels**: automation, github, monitoring, project-v2

---

### 10. Testing Infrastructure
**Title**: Expand test coverage for ingestion pipeline
**Body**:
Current test suite in `test_minimal.py` covers basic functionality but needs expansion for the complex ingestion pipeline.

**Current Coverage**:
- Database connections ✅
- API connectivity ✅
- Basic data transformation ✅

**Missing Coverage**:
- Rate limiting logic
- Parallel processing
- Error recovery mechanisms
- Data validation edge cases
- Monitoring system integration

**Labels**: testing, infrastructure, coverage, project-v2

---

## Summary

These issues represent a comprehensive roadmap for improving the OpenDiscourse project:

1. **Critical fixes** to resolve current ingestion failures
2. **Medium priority improvements** for code quality and monitoring
3. **Project v2 enhancements** for advanced features
4. **Infrastructure improvements** for automation and testing

The issues should be prioritized based on business impact, with the Congress Bills ingestion fix being the top priority due to it being a core functionality that's currently broken.
