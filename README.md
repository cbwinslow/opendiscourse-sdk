# OpenDiscourse

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-14+-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

OpenDiscourse is a legislative data ingestion and analysis platform that processes government documents from multiple sources including Congress.gov, GovInfo, and OpenStates APIs.

## 🎯 **CURRENT STATUS**

**Working Systems:**
- ✅ Congress Members: 725 records (Congresses 116, 117, 118)
- ✅ OpenStates People: 1,752 records across 9 states
- ✅ Database Connection & API Integration

**Current Issue:**
- ❌ Congress Bills: Foreign key constraint violation (chamber mapping)

**📋 IMMEDIATE PRIORITY:** Fix bills ingestion using minimal approach

---

## 🚀 **QUICK START FOR AI AGENTS**

### **MANDATORY FIRST STEPS (Read in order):**

1. **📖 Agent Handoff Guide** - Session context and current status
   ```bash
   cat docs/AGENT_HANDOFF.md
   ```

2. **📋 Documentation Index** - Complete project overview
   ```bash
   cat DOCUMENTATION_INDEX.md
   ```

3. **📝 Tasks** - Current execution plan
   ```bash
   cat docs/TASKS.md
   ```

4. **🧪 Run Tests** - Verify system state
   ```bash
   python test_minimal.py
   ```

5. **📊 Check Database** - Verify data integrity
   ```bash
   psql -d opendiscourse -c "SELECT 'Congress Members' as type, count(*) as count FROM congress.members UNION ALL SELECT 'Congress Bills', count(*) FROM congress.bills UNION ALL SELECT 'OpenStates People', count(*) FROM openstates.people UNION ALL SELECT 'Jurisdictions', count(*) FROM openstates.jurisdictions;"
   ```

---

## 📁 **PROJECT STRUCTURE**

```text
opendiscourse/
├── 📚 DOCUMENTATION INDEX
├── 📖 docs/
│   ├── 🤖 AGENT_HANDOFF.md          # ⭐ READ FIRST - Session context
│   ├── 📋 TASKS.md                  # ⭐ READ THIRD - Execution plan
│   ├── 📔 journal/
│   │   └── JOURNAL_2025_11_26.md    # Session history
│   ├── 🔄 workflows/
│   │   └── INGESTION_WORKFLOW.md     # Process documentation
│   └── 🤖 rag/
│       └── RAG_SETUP.md              # Vector database setup
├── 🧪 test_minimal.py              # ⭐ RUN FIRST - System validation
├── 🔧 cli_tool.py                   # Simplified CLI tool
├── 📜 agents.md                     # AI agent mandates
├── 📋 .windsurfrules                # Database protection rules
├── 📂 scripts/                      # Ingestion scripts
└── 📊 SESSION_COMPLETION.md         # Session summary
```

---

## 🔧 **DEVELOPMENT SETUP**

### **Prerequisites**
- Python 3.13+
- PostgreSQL 14+ with pgvector extension
- Valid API keys for Congress.gov, OpenStates, GovInfo

### **Installation**
```bash
# 1. Clone repository
git clone <repo_url>
cd opendiscourse

# 2. Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env with your API keys

# 4. Test setup
python test_minimal.py
```

---

## 🎯 **CURRENT WORK: DATA INGESTION**

### **Data Sources**
- **Congress.gov**: Members and bills (Congresses 116, 117, 118)
- **OpenStates**: State legislators across 9 states
- **GovInfo**: Federal documents (planned)

### **Database Schema**
```sql
congress.members      -- 725 records ✅
congress.bills        -- 0 records ❌ (fixing)
openstates.people     -- 1,752 records ✅
openstates.jurisdictions -- 62 records ✅
```

### **Known Issues**
- **Chamber Mapping**: API returns "House" but DB expects "house"
- **Solution**: Simple mapping in data transformation layer

---

## 📖 **IMPORTANT DOCUMENTATION**

### **For AI Agents (Mandatory Reading)**
- **[docs/AGENT_HANDOFF.md](docs/AGENT_HANDOFF.md)** - Complete session handoff
- **[docs/TASKS.md](docs/TASKS.md)** - Current execution plan
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Master index

### **Technical Documentation**
- **[agents.md](agents.md)** - AI agent mandates and database standards
- **[docs/workflows/INGESTION_WORKFLOW.md](docs/workflows/INGESTION_WORKFLOW.md)** - Ingestion procedures
- **[docs/rag/RAG_SETUP.md](docs/rag/RAG_SETUP.md)** - Vector database setup

### **Project Tracking**
- **[docs/journal/JOURNAL_2025_11_26.md](docs/journal/JOURNAL_2025_11_26.md)** - Session journal
- **[docs/CHANGELOG.md](docs/CHANGELOG.md)** - Complete change history
- **[SESSION_COMPLETION.md](SESSION_COMPLETION.md)** - Session summary

---

## 🧪 **TESTING**

### **Run Test Suite**
```bash
# Run all tests
python test_minimal.py

# Expected results: 8/9 tests passing
# 1 failing test: Chamber mapping (known issue)
```

### **Database Validation**
```bash
# Check current data status
psql -d opendiscourse -c "
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
FROM openstates.jurisdictions;"
```

---

## 🤖 **AI AGENT GUIDELINES**

### **Database Connection Standards (MANDATORY)**
```python
# ✅ CORRECT - ALWAYS USE
conn = psycopg2.connect(
    database='opendiscourse',  # NEVER 'cbwinslow'
    user='cbwinslow',
    host='/var/run/postgresql'  # NEVER 'localhost'
)

# ❌ FORBIDDEN PATTERNS
conn = psycopg2.connect(database='cbwinslow')  # WRONG DATABASE
conn = psycopg2.connect(host='localhost')      # WRONG HOST
```

### **API Key Standards (MANDATORY)**
```python
# ✅ CORRECT - ALWAYS USE
api_key = os.getenv('CONGRESS_API_KEY')
if not api_key or 'DEMO' in api_key.upper():
    raise ValueError("Valid API key required")

# ❌ FORBIDDEN
api_key = "DEMO_KEY"  # Never use demo keys
```

### **Critical Rules**
- **NEVER** restart PostgreSQL services automatically
- **NEVER** use `DROP DATABASE` commands
- **ALWAYS** validate API keys before ingestion
- **ALWAYS** use correct database connection parameters

---

## 🚀 **NEXT STEPS**

### **Immediate (Next Session)**
1. Fix chamber mapping test in `test_minimal.py`
2. Create minimal bills ingestion script
3. Test with small batch (10 bills)
4. Scale to full Congress 118 ingestion

### **Medium Term**
- Set up PGVector for documentation search
- Add Congress 116 & 117 bills
- Continue OpenStates expansion
- Performance optimization

---

## 📞 **SUPPORT**

- **Issues**: Check [docs/AGENT_HANDOFF.md](docs/AGENT_HANDOFF.md) for current status
- **Documentation**: See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete guide
- **Context**: Review [docs/journal/JOURNAL_2025_11_26.md](docs/journal/JOURNAL_2025_11_26.md) for session history

---

## 📄 **LICENSE**

MIT License - see [LICENSE](LICENSE) file for details.

---

**Last Updated**: 2025-11-26
**Current Focus**: Fix Congress bills ingestion
**Status**: Ready for execution phase

**🤖 AI AGENTS: Start with docs/AGENT_HANDOFF.md → DOCUMENTATION_INDEX.md → docs/TASKS.md → test_minimal.py**
