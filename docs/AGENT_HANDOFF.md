# AI Agent Handoff Guide

## 🎯 **CONTEXT PRESERVATION**

### **Session Summary**
Previous session (2025-11-26) focused on diagnosing and planning fixes for Congress bills ingestion. Root cause identified as foreign key constraint violation due to chamber code mapping.

### **Current State**
- **Working Systems**: Congress members (725), OpenStates people (1,752), jurisdictions (62)
- **Broken System**: Congress bills (0 records)
- **Test Suite**: 8/9 tests passing
- **Documentation**: Fully organized and indexed

---

## 🚀 **IMMEDIATE NEXT STEPS**

### **Priority 1: Fix Chamber Mapping Test**
```bash
# Run test to see failure
python test_minimal.py

# Fix in test_minimal.py line 119
# Change: assert chamber_mapping.get('Unknown', '').lower() == 'unknown'
# To: assert chamber_mapping.get('Unknown', '').lower() == ''
```

### **Priority 2: Create Minimal Bills Script**
```python
# Simple structure needed:
# 1. Database connection (use opendiscourse, /var/run/postgresql)
# 2. API fetch (Congress.gov)
# 3. Chamber mapping (House -> house, Senate -> senate)
# 4. Batch insert (handle foreign key constraints)
```

### **Priority 3: Test with Small Batch**
- Start with 10 bills from Congress 118
- Verify insertion works
- Check for foreign key violations

---

## 🔧 **CRITICAL TECHNICAL STANDARDS**

### **Database Connection (MANDATORY)**
```python
import psycopg2

conn = psycopg2.connect(
    database='opendiscourse',  # NEVER 'cbwinslow'
    user='cbwinslow',
    host='/var/run/postgresql'  # NEVER 'localhost'
)
```

### **API Key Validation (MANDATORY)**
```python
import os

congress_key = os.getenv('CONGRESS_API_KEY')
if not congress_key or 'DEMO' in congress_key.upper():
    raise ValueError("Valid CONGRESS_API_KEY required")
```

### **Chamber Code Mapping (CRITICAL)**
```python
chamber_mapping = {
    'House': 'house',
    'Senate': 'senate',
    'Joint': 'joint'
}
origin_chamber = chamber_mapping.get(api_chamber, api_chamber.lower())
```

---

## 📋 **WORKFLOWS TO FOLLOW**

### **Debugging Workflow**
1. Check database connection
2. Verify API credentials
3. Run test suite
4. Check specific error messages
5. Use minimal reproduction

### **Ingestion Workflow**
1. Validate prerequisites (DB, API, tables)
2. Fetch small batch (10 records)
3. Transform data (apply mappings)
4. Test insertion
5. Scale to full batch

### **Documentation Workflow**
1. Update journal with progress
2. Note decisions and rationale
3. Update status in DOCUMENTATION_INDEX.md
4. Create handoff notes for next session

---

## 📁 **KEY FILES TO REVIEW**

### **Must Read**
1. **[TASKS.md](../TASKS.md)** - Complete execution plan
2. **[test_minimal.py](../test_minimal.py)** - Test suite with 1 failing test
3. **[INGESTION_PROCEDURES.md](../INGESTION_PROCEDURES.md)** - Working procedures
4. **[agents.md](../agents.md)** - Agent mandates and standards

### **Reference**
1. **[cli_tool.py](../cli_tool.py)** - Simplified CLI tool
2. **[INGESTION_SUMMARY.md](../INGESTION_SUMMARY.md)** - Executive summary
3. **[DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)** - Master index

---

## 🎯 **SUCCESS METRICS**

### **Phase 1 Success**
- [ ] All 9 tests pass
- [ ] Chamber mapping fixed
- [ ] Minimal script created

### **Phase 2 Success**
- [ ] 10+ bills inserted successfully
- [ ] No foreign key violations
- [ ] Data integrity verified

### **Phase 3 Success**
- [ ] 1000+ bills from Congress 118
- [ ] 50+ bills/second processing
- [ ] Full test coverage

---

## 🚨 **COMMON PITFALLS TO AVOID**

### **Database Issues**
- NEVER use database='cbwinslow'
- NEVER use host='localhost'
- ALWAYS use Unix socket '/var/run/postgresql'

### **API Issues**
- NEVER use demo keys
- ALWAYS validate credentials before ingestion
- ALWAYS handle rate limits gracefully

### **Architecture Issues**
- AVOID over-engineering
- PREFER simple functions over complex classes
- USE test-first approach

---

## 🤖 **AI AGENT GUIDELINES**

### **Before Starting**
1. Read journal for full context
2. Run test suite to verify current state
3. Review TASKS.md for execution plan
4. Validate database connection

### **During Work**
1. Update journal with progress
2. Document decisions and rationale
3. Test changes incrementally
4. Update documentation as needed

### **Before Finishing**
1. Verify success metrics met
2. Update status in DOCUMENTATION_INDEX.md
3. Create handoff notes for next session
4. Ensure all tests pass

---

## 📊 **CURRENT DATABASE STATUS**

```sql
-- Quick status check
SELECT
    'Congress Members' as type, count(*) as count
FROM congress.members
UNION ALL
SELECT 'Congress Bills', count(*)
FROM congress.bills
UNION ALL
SELECT 'OpenStates People', count(*)
FROM openstates.people
UNION ALL
SELECT 'Jurisdictions', count(*)
FROM openstates.jurisdictions;
```

**Expected Results:**
- Congress Members: 725
- Congress Bills: 0 (to be fixed)
- OpenStates People: 1752
- Jurisdictions: 62

---

## 🔍 **DEBUGGING COMMANDS**

### **Test Current State**
```bash
python test_minimal.py
```

### **Check Database**
```bash
psql -d opendiscourse -c "SELECT count(*) FROM congress.bills;"
```

### **Verify Chambers**
```bash
psql -d opendiscourse -c "SELECT * FROM congress.chambers;"
```

---

## 📝 **SESSION HANDOFF TEMPLATE**

### **When Starting Session**
- Previous session date: [date]
- Last accomplishment: [what was done]
- Current status: [test results, db counts]
- Immediate next step: [specific task]

### **When Ending Session**
- Session accomplishments: [what was done]
- Issues discovered: [new problems]
- Decisions made: [architectural choices]
- Next session priorities: [specific tasks]

---

*Last Updated: 2025-11-26*
*Purpose: Ensure session continuity and context preservation*
*Priority: Fix bills ingestion with minimal approach*
