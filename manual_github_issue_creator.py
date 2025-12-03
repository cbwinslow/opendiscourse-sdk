#!/usr/bin/env python3
"""
Manual GitHub Issue Creation Helper
Provides formatted content for manual GitHub issue creation
"""

def print_issue_instructions():
    """Print instructions for creating GitHub issues manually"""

    print("🚀 MANUAL GITHUB ISSUE CREATION INSTRUCTIONS")
    print("=" * 60)
    print()
    print("Due to GitHub API authentication issues, please create the following issues manually:")
    print()
    print("1. Go to: https://github.com/cbwinslow/opendiscourse/issues/new/choose")
    print("2. For each issue below:")
    print("   - Copy the title and paste it in the title field")
    print("   - Copy the body content and paste it in the body field")
    print("   - Add the specified labels")
    print("   - Click 'Submit new issue'")
    print()
    print("3. After creating all issues, go to Project v2 and:")
    print("   - Create a new project called 'Ingestion System Fixes'")
    print("   - Add columns: Critical, High Priority, In Progress, Completed")
    print("   - Link all created issues to the project")
    print()
    print("=" * 60)
    print()

def print_issue_1():
    """Print Issue #1 content"""
    title = "🚨 CRITICAL: Congress Bills Ingestion Complete Failure"

    body = '''## 🚨 **CRITICAL: Congress Bills Ingestion Complete Failure**

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
**Labels**: bug, ingestion, congress, priority-critical'''

    labels = "bug, ingestion, congress, priority-critical"

    print(f"ISSUE #1:")
    print(f"Title: {title}")
    print(f"Labels: {labels}")
    print(f"Body:")
    print(body)
    print("\n" + "="*60 + "\n")

def print_issue_2():
    """Print Issue #2 content"""
    title = "Script Parameter Mismatches - Comprehensive Bulk Ingestion Failure"

    body = '''## Script Parameter Mismatches - Comprehensive Bulk Ingestion Failure

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
**Labels**: bug, ingestion, parameters, priority-critical'''

    labels = "bug, ingestion, parameters, priority-critical"

    print(f"ISSUE #2:")
    print(f"Title: {title}")
    print(f"Labels: {labels}")
    print(f"Body:")
    print(body)
    print("\n" + "="*60 + "\n")

def print_issue_3():
    """Print Issue #3 content"""
    title = "OpenStates Command Structure Issues - 60 Jobs Failing"

    body = '''## OpenStates Command Structure Issues - 60 Jobs Failing

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
**Labels**: bug, openstates, ingestion, priority-high'''

    labels = "bug, openstates, ingestion, priority-high"

    print(f"ISSUE #3:")
    print(f"Title: {title}")
    print(f"Labels: {labels}")
    print(f"Body:")
    print(body)
    print("\n" + "="*60 + "\n")

def main():
    """Main function to print all issues"""
    print_issue_instructions()
    print_issue_1()
    print_issue_2()
    print_issue_3()

    print("📋 PROJECT V2 SETUP INSTRUCTIONS:")
    print("=" * 60)
    print("1. Go to GitHub Projects and create new Project v2")
    print("2. Name: 'Ingestion System Fixes'")
    print("3. Add columns:")
    print("   - 🔴 Critical Issues")
    print("   - 🟡 High Priority")
    print("   - 📊 In Progress")
    print("   - ✅ Completed")
    print("4. Add all 3 issues to the project board")
    print("5. Link issue #1 to issue #4 (database connections) as dependency")
    print()
    print("🎯 NEXT STEPS:")
    print("1. Create the 3 GitHub issues using the content above")
    print("2. Set up Project v2 board")
    print("3. Start with Issue #1 (Congress Bills) - it's the most critical")
    print("4. Test fixes thoroughly before proceeding to next issue")
    print()
    print("📊 EXPECTED OUTCOMES:")
    print("- Issue #1 fixed: Congress Bills ingestion working")
    print("- Issue #2 fixed: Bulk ingestion success rate > 90%")
    print("- Issue #3 fixed: OpenStates jobs completing successfully")
    print("- Overall: Complete ingestion system functional")
    print()
    print("🚀 READY TO START!")

if __name__ == "__main__":
    main()
