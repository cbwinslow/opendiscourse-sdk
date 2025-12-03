#!/usr/bin/env python3
"""
Create GitHub Issues for OpenDiscourse Project
Uses GitHub REST API via curl to avoid dependency issues
"""

import os
import json
import subprocess
from datetime import datetime

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "cbwinslow/opendiscourse"

# Issue definitions (simplified for API)
ISSUES = [
    {
        "title": "🚨 Critical: Congress Bills ingestion fails due to chamber mapping foreign key constraint",
        "body": """## Current Status
The Congress Bills ingestion is currently failing with foreign key constraint violations related to chamber mapping. The API returns "House" but the database expects "house" (lowercase).

**Data Status:**
- ✅ Congress Members: 725 records (working)
- ❌ Congress Bills: 0 records (failing)
- ✅ OpenStates People: 1,752 records (working)

## Steps to Reproduce
1. Run `python test_minimal.py` - Chamber mapping test fails
2. Attempt Congress Bills ingestion - Foreign key constraint violation

## Expected Fix
Implement proper chamber mapping in the data transformation layer.

This is blocking the core Congress data ingestion functionality.

**Affected Files:**
- test_minimal.py:104-120 (chamber mapping test)
- scripts/ingest_congress_bills_incremental.py (ingestion script)
- Database schema: congress.chambers table""",
        "labels": ["bug", "ingestion", "congress", "priority-high"]
    },
    {
        "title": "⚡ High: Enhanced OpenStates ingestion - Missing implementation methods",
        "body": """## Issue
The `scripts/enhanced_openstates_ingestion.py` file contains sophisticated infrastructure for parallel processing, rate limiting, and data validation, but several core ingestion methods are not implemented (just placeholders).

## Missing Implementations
- `ingest_person_details()` - Person details enrichment (line 819)
- `ingest_person_bill_relationships()` - Person-bill relationships (line 824)
- `ingest_bills_with_details()` - Bills ingestion (line 829)
- `ingest_committees_with_details()` - Committees ingestion (line 834)
- `ingest_events_with_details()` - Events ingestion (line 839)

## Current Status
- ✅ Basic people ingestion: Working
- ❌ Enhanced data types: Not implemented (placeholder methods)

## Expected Fix
Implement the placeholder methods in `scripts/enhanced_openstates_ingestion.py` lines 819-842 to complete the enhanced OpenStates ingestion pipeline.""",
        "labels": ["enhancement", "openstates", "ingestion", "priority-high"]
    },
    {
        "title": "📊 Medium: Monitoring system issues - Delegate mismatch and error recovery",
        "body": """## Issues Identified

### Issue 3a: Delegate Registration Mismatch for Congress Member Terms
- **Location**: monitoring/delegates.py:72-85 vs scripts/ingest_members_monitored.py:345-366
- **Problem**: Inconsistent progress tracking for term data
- **Impact**: Missing monitoring for term insertions

### Issue 3b: Missing Error Recovery Mechanism
- **Location**: scripts/ingest_members_monitored.py:378-398
- **Problem**: No retry logic for failed database insertions
- **Impact**: Batch rollback loses all data instead of quarantining failed records

### Issue 3c: Progress Percentage Calculation Flaw
- **Location**: monitoring/progress_monitor.py:216
- **Problem**: Can show progress > 100% when total_estimated is None
- **Impact**: Misleading progress reporting

### Issue 3d: Missing Monitoring for GovInfo Delegates
- **Location**: monitoring/delegates.py:72-83
- **Problem**: Delegate registered but not integrated with actual workflows
- **Impact**: Unused monitoring capability

## Affected Files
- monitoring/delegates.py
- monitoring/progress_monitor.py
- scripts/ingest_members_monitored.py""",
        "labels": ["monitoring", "bug", "database", "priority-medium"]
    },
    {
        "title": "🔧 Medium: Database connection standards violations",
        "body": """## Issue
Found multiple instances of incorrect database connection patterns that don't follow the project's standards.

## Current Standards (from agents.md)
```python
# ✅ CORRECT
conn = psycopg2.connect(
    database='opendiscourse',  # NEVER 'cbwinslow'
    user='cbwinslow',
    host='/var/run/postgresql'  # NEVER 'localhost'
)
```

## Found Issues
- `scripts/enhanced_openstates_ingestion.py:530-533` uses wrong database name 'cbwinslow'
- Multiple files may have similar issues

## Required Fix
Audit all database connections across the codebase to ensure they follow the correct patterns specified in `agents.md`.

## Impact
Improper database connections can cause:
- Connection failures
- Data access issues
- Security vulnerabilities
- Environment inconsistencies""",
        "labels": ["database", "standards", "code-quality", "priority-medium"]
    },
    {
        "title": "🛠️ Enhancement: Complete PGVector integration for semantic search",
        "body": """## Current Status
The project has RAG setup documentation but needs full PGVector integration for semantic search across ingested documents.

**Current State:**
- ✅ RAG setup documented in docs/rag/RAG_SETUP.md
- ✅ PGVector mentioned in requirements
- ❌ Integration not complete

## Required Work
1. **Complete PGVector setup and configuration**
   - Install and configure PGVector extension
   - Create vector storage tables
   - Set up embedding pipeline

2. **Implement document embedding pipeline**
   - Process ingested documents
   - Generate embeddings using text-embedding-3-small
   - Store vectors in PostgreSQL with PGVector

3. **Create semantic search endpoints**
   - Vector similarity queries
   - Hybrid search (semantic + keyword)
   - Search result ranking and filtering

4. **Integration with existing data**
   - Congress documents
   - OpenStates data
   - GovInfo materials

## Project v2 Alignment
This is a core component of the Project v2 enhancement for advanced document search and RAG capabilities.""",
        "labels": ["enhancement", "vector-database", "rag", "project-v2"]
    },
    {
        "title": "🏛️ Enhancement: Expand Congress data ingestion to include historical data",
        "body": """## Current Coverage
- ✅ Congress Members: 725 records (Congresses 116, 117, 118)
- ❌ Congress Bills: 0 records (currently broken)

## Enhancement Goals
1. **Fix current bills ingestion** (Priority 1)
   - Resolve chamber mapping issue (Issue #1)
   - Complete Congress 118 bills ingestion

2. **Add historical Congress data** (Priority 2)
   - Congress 115 and earlier data
   - Historical member information
   - Past congressional sessions

3. **Additional data types** (Priority 3)
   - Roll call votes
   - Committee data and memberships
   - Amendment data and tracking
   - Congressional Record entries
   - Floor proceedings

4. **Enhanced metadata** (Priority 4)
   - Bill relationships and companions
   - Policy area classifications
   - Sponsor networks and co-sponsorship analysis

## API Resources
- Congress.gov API v3 for current data
- GovInfo API for historical documents
- Bulk data downloads for large-scale ingestion

## Project v2 Impact
This expansion is essential for comprehensive legislative analysis and historical trend identification.""",
        "labels": ["enhancement", "congress", "historical-data", "project-v2"]
    },
    {
        "title": "🧹 Cleanup: OpenStates scrapers have TODO comments needing attention",
        "body": """## Issue Analysis
Found 144 TODO/FIXME/BUG comments across the OpenStates scrapers that need addressing.

## Major Categories

### Session Date Updates (Multiple jurisdictions)
- `openstates-scrapers/scrapers/nh/bills.py:405` - Fake vote passing logic needs real implementation
- `openstates-scrapers/scrapers/mo/__init__.py:86-87` - Real end dates needed
- `openstates-scrapers/scrapers/nm/__init__.py:204` - Correct start date needed
- Multiple other scrapers have similar date TODO comments

### Vote Processing Improvements
- `openstates-scrapers/scrapers/nc/bills.py:205` - Vote scraper needs fixing
- `openstates-scrapers/scrapers/ma/votes.py:177` - Vote bill_id processing needs work
- `openstates-scrapers/scrapers/nd/bills.py:225` - Classification types need expansion

### Committee Data Enhancements
- `openstates-scrapers/scrapers_next/vt/committees.py:96` - HTML link consistency
- `openstates-scrapers/scrapers_next/ri/people.py:7` - Bio page URL fixes

### Error Handling Improvements
- `openstates-scrapers/scrapers/il/bills.py:691` - Better error catching for vote processing
- `openstates-scrapers/scrapers/vt/__init__.py:124` - Year slug function verification

## Priority Areas
1. **High**: Vote processing and session dates (affects data quality)
2. **Medium**: Committee and people data improvements
3. **Low**: Minor enhancements and cleanup

## Impact
Addressing these TODOs will improve:
- Data accuracy and completeness
- Scraping reliability
- Maintenance burden
- User experience""",
        "labels": ["openstates", "scrapers", "cleanup", "project-v2"]
    },
    {
        "title": "🤖 Enhancement: Improve GitHub integration automation",
        "body": """## Current Capabilities
The project has a solid GitHub sync setup (`scripts/github_sync_setup.py`) that creates labels and milestones:

- ✅ Labels and milestones setup
- ✅ Agent log parsing script exists
- ✅ Issue templates configured in .github/ISSUE_TEMPLATE/

## Enhancement Goals

### 1. Automate Monitoring Issue Creation
- Connect monitoring system directly to GitHub
- Automatic issue creation from monitoring failures
- Progress tracking integration

### 2. Enhanced Issue Templates
- Create templates for common ingestion patterns
- Automated issue linking and referencing
- Milestone tracking for ingestion progress

### 3. Agent Integration Improvements
- Real-time issue updates from AI agents
- Automated status tracking
- Progress reporting integration

### 4. Workflow Automation
- Auto-assign issues based on content
- Automated labeling based on file patterns
- Progress milestone updates

## Implementation
- Enhance existing `scripts/github_sync_setup.py`
- Improve `github_sync_package/scripts/agent_log_issue_sync.py`
- Add new automation scripts for monitoring integration

## Project v2 Benefits
Better automation will support the enhanced Project v2 features and reduce manual overhead.""",
        "labels": ["automation", "github", "monitoring", "project-v2"]
    },
    {
        "title": "🧪 Enhancement: Expand test coverage for ingestion pipeline",
        "body": """## Current Coverage
The test suite in `test_minimal.py` covers basic functionality but needs expansion for the complex ingestion pipeline.

**Current Coverage:**
- ✅ Database connections
- ✅ API connectivity
- ✅ Basic data transformation

## Missing Test Coverage

### 1. Rate Limiting Logic
- OpenStates API rate limiting (1000 requests/hour)
- Adaptive rate limiting behavior
- Error recovery and backoff mechanisms

### 2. Parallel Processing
- Thread coordination in `OpenStatesParallelProcessor`
- Rate limit coordination between threads
- Error handling in parallel contexts

### 3. Data Validation
- Pydantic model validation edge cases
- Data transformation error scenarios
- Schema validation for different data formats

### 4. Monitoring System Integration
- Delegate registration and tracking
- Progress calculation accuracy
- Error reporting and logging

### 5. Recovery Mechanisms
- Database connection retry logic
- Batch insertion error handling
- Partial failure recovery scenarios

## Test Infrastructure Needs
- Mock API responses for testing
- Database test fixtures
- Rate limiting test scenarios
- Parallel processing test frameworks

## Benefits
- Higher confidence in ingestion reliability
- Faster debugging of issues
- Better regression detection
- Improved code quality""",
        "labels": ["testing", "infrastructure", "coverage", "project-v2"]
    },
    {
        "title": "📚 Documentation: Update data validation and processing improvements",
        "body": """## Issues Identified

### 1. Hardcoded State Mapping
- **Location**: scripts/ingest_members_monitored.py:213-228
- **Problem**: State name to code mapping is hardcoded
- **Impact**: Difficult to maintain and extend
- **Fix**: Make database-driven configuration

### 2. Redundant Date Parsing Logic
- **Location**: scripts/ingest_members_monitored.py:270-282
- **Problem**: Both if/else branches perform identical parsing
- **Impact**: Unnecessary complexity, potential bugs
- **Fix**: Remove redundant conditional logic

### 3. Throughput Calculation Edge Case
- **Location**: monitoring/progress_monitor.py:175
- **Problem**: Uses arbitrary 0.01 minute minimum
- **Impact**: Skewed initial throughput calculations
- **Fix**: Use more accurate minimum calculation

### 4. Missing Error Recovery Documentation
- **Location**: Multiple ingestion scripts
- **Problem**: No documented retry strategies
- **Impact**: Unclear failure recovery approaches
- **Fix**: Document and implement retry policies

## Documentation Updates Needed
1. Add error handling guidelines
2. Document data transformation patterns
3. Create validation best practices guide
4. Update API integration documentation

## Code Quality Impact
These improvements will enhance:
- Code maintainability
- Error handling clarity
- Performance monitoring accuracy
- Development workflow efficiency""",
        "labels": ["documentation", "maintainability", "data-processing", "priority-medium"]
    }
]

def create_github_issues_curl():
    """Create GitHub issues using curl and GitHub REST API"""
    try:
        print(f"Creating {len(ISSUES)} GitHub issues for {REPO}")

        created_issues = []

        for issue_data in ISSUES:
            try:
                # Prepare the data for the API call
                issue_json = {
                    "title": issue_data["title"],
                    "body": issue_data["body"],
                    "labels": issue_data["labels"]
                }

                # Use curl to call GitHub API
                cmd = [
                    "curl", "-X", "POST",
                    f"https://api.github.com/repos/{REPO}/issues",
                    "-H", f"Authorization: token {GITHUB_TOKEN}",
                    "-H", "Accept: application/vnd.github.v3+json",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(issue_json)
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    created_issues.append({
                        "number": response.get("number"),
                        "title": response.get("title"),
                        "url": response.get("html_url"),
                        "labels": [label["name"] for label in response.get("labels", [])]
                    })
                    print(f"✅ Created issue #{response.get('number')}: {response.get('title')}")
                else:
                    print(f"❌ Failed to create issue: {issue_data['title'][:50]}... - {result.stderr}")

            except Exception as e:
                print(f"❌ Exception creating issue: {issue_data['title'][:50]}... - {e}")

        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "repository": REPO,
            "total_issues": len(ISSUES),
            "created_issues": created_issues,
            "failed_issues": len(ISSUES) - len(created_issues)
        }

        with open("github_issues_created.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n🎉 Successfully created {len(created_issues)} issues!")
        print(f"📄 Results saved to: github_issues_created.json")

        return results

    except Exception as e:
        print(f"❌ GitHub API call failed: {e}")
        return None

if __name__ == "__main__":
    # Check for GitHub token
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN environment variable not found")
        print("💡 Set it with: export GITHUB_TOKEN='your_token_here'")
        print("📝 Token needs 'repo' permissions to create issues")
        exit(1)

    # Create the issues
    results = create_github_issues_curl()

    if results:
        print(f"\n📊 Summary:")
        print(f"   Repository: {results['repository']}")
        print(f"   Issues created: {len(results['created_issues'])}")
        print(f"   Failed: {results['failed_issues']}")
        print(f"   Timestamp: {results['timestamp']}")
    else:
        print("\n❌ Failed to create issues. Check GitHub token and permissions.")
