#!/usr/bin/env python3
"""
Simple GitHub Issue Creation for OpenDiscourse Ingestion Issues
Creates critical GitHub issues for ingestion problems
"""

import os
import json
import requests
from datetime import datetime

def create_github_issue(title, body, labels, token, repo_owner="cbwinslow", repo_name="opendiscourse"):
    """Create a GitHub issue"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    data = {
        "title": title,
        "body": body,
        "labels": labels
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Failed to create issue '{title}': {response.status_code} - {response.text}")
        return None

def main():
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN environment variable required")
        print("Set it with: export GITHUB_TOKEN=your_token_here")
        return

    # Issue 1: Congress Bills Ingestion Failure
    issue1_title = "🚨 CRITICAL: Congress Bills Ingestion Complete Failure"
    issue1_body = """## 🚨 **CRITICAL: Congress Bills Ingestion Complete Failure**

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

---
**Priority**: 🔴 Critical
**Labels**: bug, ingestion, congress, priority-critical"""

    issue1_labels = ["bug", "ingestion", "congress", "priority-critical"]

    # Issue 2: Script Parameter Mismatches
    issue2_title = "Script Parameter Mismatches - Comprehensive Bulk Ingestion Failure"
    issue2_body = """## Script Parameter Mismatches - Comprehensive Bulk Ingestion Failure

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

---
**Priority**: 🔴 Critical
**Labels**: bug, ingestion, parameters, priority-critical"""

    issue2_labels = ["bug", "ingestion", "parameters", "priority-critical"]

    # Issue 3: OpenStates Command Structure
    issue3_title = "OpenStates Command Structure Issues - 60 Jobs Failing"
    issue3_body = """## OpenStates Command Structure Issues - 60 Jobs Failing

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

### **Correct Command Structures**
```bash
# People ingestion:
python3 scripts/ingestion/openstates_cli.py ingest-people --jurisdiction ca

# Bills ingestion:
python3 scripts/ingestion/openstates_cli.py ingest-bills --jurisdiction ca

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

---
**Priority**: 🟡 High
**Labels**: bug, openstates, ingestion, priority-high"""

    issue3_labels = ["bug", "openstates", "ingestion", "priority-high"]

    # Create the issues
    issues_to_create = [
        (issue1_title, issue1_body, issue1_labels),
        (issue2_title, issue2_body, issue2_labels),
        (issue3_title, issue3_body, issue3_labels)
    ]

    created_issues = []
    for title, body, labels in issues_to_create:
        print(f"📝 Creating issue: {title}")
        result = create_github_issue(title, body, labels, token)
        if result:
            created_issues.append(result)
            print(f"✅ Created issue #{result['number']}")
        else:
            print(f"❌ Failed to create issue")

    print(f"\n🎉 Created {len(created_issues)} new issues")
    print("📊 Summary:")
    for issue in created_issues:
        print(f"   - #{issue['number']}: {issue['title']}")

    return created_issues

if __name__ == "__main__":
    print("🚀 Creating GitHub Issues for OpenDiscourse Ingestion Problems")
    print("=" * 60)
    main()
