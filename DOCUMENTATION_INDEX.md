# OpenDiscourse Documentation Index

## 📚 **TABLE OF CONTENTS**

### **🎯 QUICK START**
- [Current Status Summary](#current-status-summary)
- [Immediate Next Steps](#immediate-next-steps)
- [Critical Issues](#critical-issues)

### **📊 PROJECT OVERVIEW**
- [Project Goals](docs/PROJECT_OVERVIEW.md)
- [Architecture Overview](docs/technical/ARCHITECTURE.md)
- [Database Schema](docs/technical/DATABASE_SCHEMA.md)

### **🔧 OPERATIONAL GUIDES**
- [Ingestion Procedures](INGESTION_PROCEDURES.md)
- [Agent Mandates](agents.md)
- [Git Operations Guide](agents.md#-git-operations-and-security-agent)
- [CLI Runtime Metadata Guide](docs/CLI_RUNTIME_METADATA.md)
- [Project Rules](.windsurfrules)
- [Task Management](TASKS.md)

### **📋 WORKFLOWS & PROCESSES**
- [Ingestion Workflow](docs/workflows/INGESTION_WORKFLOW.md)
- [Debugging Workflow](docs/workflows/DEBUGGING_WORKFLOW.md)
- [Testing Workflow](docs/workflows/TESTING_WORKFLOW.md)
- [Documentation Process](docs/workflows/DOCUMENTATION_PROCESS.md)

### **🧪 TESTING & QUALITY**
- [Test Suite](test_minimal.py)
- [Test Results](docs/technical/TEST_RESULTS.md)
- [Quality Standards](docs/technical/QUALITY_STANDARDS.md)

### **📖 JOURNAL & LOGS**
- [Session Journal](docs/journal/JOURNAL_2025_11_26.md)
- [Change Log](CHANGELOG.md)
- [Progress Tracking](docs/journal/PROGRESS_LOG.md)

### **🤖 AI AGENT GUIDANCE**
- [Agent Handoff Guide](docs/AGENT_HANDOFF.md)
- [Context Preservation](docs/CONTEXT_PRESERVATION.md)
- [RAG Database Setup](docs/rag/RAG_SETUP.md)

---

## 🎯 **CURRENT STATUS SUMMARY**

### **✅ WORKING SYSTEMS**
- **Congress Members**: 725 records (Congresses 116, 117, 118)
- **OpenStates People**: 1,752 records across 9 states
- **OpenStates Jurisdictions**: 62 records
- **Database Connection**: ✅ Working
- **API Credentials**: ✅ Working
- **Test Suite**: 8/9 tests passing

### **❌ BROKEN SYSTEMS**
- **Congress Bills**: 0 records (foreign key constraint violations)
- **Complex Ingestion Scripts**: Over-engineered, hard to debug

### **🔧 ROOT CAUSES IDENTIFIED**
1. **Chamber Code Mapping**: API returns "House" but DB expects "house"
2. **Over-Complex Architecture**: Multiple layers obscuring simple issues
3. **Function Parameter Mismatches**: Checkpoint functions with wrong signatures

---

## 🚀 **IMMEDIATE NEXT STEPS**

### **PHASE 1: FIX BILLS INGESTION (30 minutes)**
1. Fix chamber mapping test
2. Create minimal bills ingestion script
3. Test with small batch (10 bills)

### **PHASE 2: SCALE & VALIDATE (1 hour)**
4. Scale to full Congress 118 ingestion
5. Add error handling
6. Verify data integrity

### **PHASE 3: OPTIMIZE & DOCUMENT (2 hours)**
7. Performance optimization
8. Comprehensive testing
9. Update documentation

---

## 🚨 **CRITICAL ISSUES**

### **HIGH PRIORITY**
- **Congress Bills Ingestion**: Foreign key constraint violations
- **Complex System Simplification**: Need minimal, testable approach

### **MEDIUM PRIORITY**
- **Documentation Organization**: Structure and accessibility
- **RAG Database Setup**: Vectorize all documentation
- **Test Coverage**: Expand test suite

### **LOW PRIORITY**
- **Performance Optimization**: After core functionality works
- **Additional States**: Continue OpenStates expansion

---

## 🤖 **FOR NEXT AI AGENT**

### **CONTEXT PRESERVATION**
- All documentation organized in `/docs/` structure
- Journal files track session progress
- RAG database setup instructions in `/docs/rag/`

### **IMMEDIATE TASKS**
1. Execute [TASKS.md](TASKS.md) starting with TASK 1.1
2. Fix chamber mapping test in [test_minimal.py](test_minimal.py)
3. Create minimal bills ingestion script

### **KEY FILES TO REVIEW**
- [TASKS.md](TASKS.md) - Complete execution plan
- [INGESTION_PROCEDURES.md](INGESTION_PROCEDURES.md) - Working procedures
- [agents.md](agents.md) - Agent mandates and database standards
- [test_minimal.py](test_minimal.py) - Test suite with 1 failing test
- [docs/CLI_RUNTIME_METADATA.md](docs/CLI_RUNTIME_METADATA.md) - Canonical CLI configs, validation commands, log locations

### **DATABASE CONNECTION STANDARDS**
```python
conn = psycopg2.connect(
    database='opendiscourse',  # NEVER 'cbwinslow'
    user='cbwinslow',
    host='/var/run/postgresql'  # NEVER 'localhost'
)
```

### **SUCCESS METRICS**
- Fix 1 failing test
- Insert 10+ bills successfully
- Scale to 1000+ bills for Congress 118
- Keep `config.toml`, `config.json`, and `version.json` valid (per [docs/CLI_RUNTIME_METADATA.md](docs/CLI_RUNTIME_METADATA.md))

---

## 📈 **PROGRESS TRACKING**

### **SESSION ACCOMPLISHMENTS**
- ✅ Diagnosed bills ingestion root cause
- ✅ Created comprehensive test suite
- ✅ Designed minimal ingestion approach
- ✅ Organized documentation structure
- ✅ Created execution plan with timelines

### **NEXT SESSION GOALS**
- Fix chamber mapping test
- Create working bills ingestion
- Verify data integrity
- Scale to full ingestion

---

*Last Updated: 2025-11-26*
*Session: Complex system diagnosis and simplification*
*Priority: Fix bills ingestion with minimal approach*
