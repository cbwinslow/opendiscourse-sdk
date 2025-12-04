# Ingestion Workflow

## 🎯 **OVERVIEW**
Standard workflow for ingesting legislative data into OpenDiscourse database.

---

## 📋 **WORKFLOW STEPS**

### **Phase 1: Pre-Ingestion Validation**

#### **Step 1.1: Environment Check**
```bash
# Check database connection
psql -d opendiscourse -c "SELECT 1;"

# Check API keys
env | grep -E "(CONGRESS|OPENSTATES|GOVINFO)_API_KEY"

# Run test suite
python test_minimal.py
```

#### **Step 1.2: Database Schema Validation**
```bash
# Verify required tables exist
psql -d opendiscourse -c "\dt congress.*"
psql -d opendiscourse -c "\dt openstates.*"
psql -d opendiscourse -c "\dt incremental.*"

# Check foreign key constraints
psql -d opendiscourse -c "SELECT * FROM congress.chambers;"
```

#### **Step 1.3: API Connectivity Test**
```bash
# Test Congress API
curl -H "X-API-Key: $CONGRESS_API_KEY" \
     "https://api.congress.gov/v3/member/congress/118?limit=1"

# Test OpenStates API
curl -H "X-API-KEY: $OPENSTATES_API_KEY" \
     "https://v3.openstates.org/people?jurisdiction=ca&limit=1"
```

---

### **Phase 2: Data Ingestion**

#### **Step 2.1: Choose Data Source**
- **Congress Members**: Use existing working script
- **Congress Bills**: Use minimal script (after fix)
- **OpenStates People**: Use existing working script
- **OpenStates Bills**: Future development

#### **Step 2.2: Prepare Database**
```bash
# Add jurisdiction if needed (OpenStates)
psql -d opendiscourse -c "INSERT INTO openstates.jurisdictions (jurisdiction_id, name, classification, state_code) VALUES ('ocd-jurisdiction/country:us/state:xx/government', 'StateName', 'state', 'xx') ON CONFLICT DO NOTHING;"
```

#### **Step 2.3: Execute Ingestion**
```bash
# Congress Members (Working)
python scripts/ingest_congress_members_incremental.py --congress 118

# OpenStates People (Working)
python scripts/ingest_openstates_people.py --jurisdiction ca

# Congress Bills (After Fix)
python minimal_bills_ingestion.py --congress 118 --limit 100
```

#### **Step 2.4: Monitor Progress**
```bash
# Check record counts
psql -d opendiscourse -c "
SELECT
    'Congress Members' as type, count(*) as count
FROM congress.members
UNION ALL
SELECT 'Congress Bills', count(*)
FROM congress.bills
UNION ALL
SELECT 'OpenStates People', count(*)
FROM openstates.people;
"

# Check for errors
psql -d opendiscourse -c "SELECT * FROM incremental.ingestion_sessions ORDER BY created_at DESC LIMIT 5;"
```

---

### **Phase 3: Post-Ingestion Validation**

#### **Step 3.1: Data Integrity Check**
```bash
# Verify no duplicate primary keys
psql -d opendiscourse -c "SELECT bioguide_id, COUNT(*) FROM congress.members GROUP BY bioguide_id HAVING COUNT(*) > 1;"

# Check foreign key constraints
psql -d opendiscourse -c "SELECT COUNT(*) FROM congress.bills WHERE origin_chamber NOT IN (SELECT chamber_code FROM congress.chambers);"
```

#### **Step 3.2: Quality Verification**
```bash
# Sample data inspection
psql -d opendiscourse -c "SELECT * FROM congress.members LIMIT 3;"
psql -d opendiscourse -c "SELECT * FROM congress.bills LIMIT 3;"
psql -d opendiscourse -c "SELECT * FROM openstates.people LIMIT 3;"
```

#### **Step 3.3: Performance Metrics**
```bash
# Check database size
psql -d opendiscourse -c "SELECT pg_size_pretty(pg_database_size('opendiscourse'));"

# Check table sizes
psql -d opendiscourse -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname IN ('congress', 'openstates') ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

---

## 🔄 **WORKFLOW DECISIONS**

### **When to Use Complex Scripts**
- **Large datasets** (>10,000 records)
- **Incremental processing** needed
- **Checkpoint recovery** required
- **Rate limiting** critical

### **When to Use Minimal Scripts**
- **Small datasets** (<1,000 records)
- **Testing and debugging**
- **Simple transformations**
- **Quick validation**

### **When to Use CLI Tool**
- **One-off operations**
- **Simple commands**
- **Status checking**
- **Quick tests**

---

## 🚨 **ERROR HANDLING**

### **Common Errors and Solutions**

#### **Database Connection Errors**
```bash
# Error: connection refused
# Solution: Check PostgreSQL status
sudo systemctl status postgresql

# Error: database does not exist
# Solution: Create database
createdb -U cbwinslow opendiscourse

# Error: permission denied
# Solution: Check user permissions
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE opendiscourse TO cbwinslow;"
```

#### **API Authentication Errors**
```bash
# Error: 401 Unauthorized
# Solution: Check API key
echo $CONGRESS_API_KEY

# Error: rate limit exceeded
# Solution: Wait and retry
sleep 60
```

#### **Foreign Key Constraint Errors**
```bash
# Error: insert violates foreign key constraint
# Solution: Check reference data exists
psql -d opendiscourse -c "SELECT * FROM congress.chambers;"
```

#### **Data Transformation Errors**
```bash
# Error: invalid input syntax for type integer
# Solution: Add data validation
# Check data before insertion
```

---

## 📊 **SUCCESS METRICS**

### **Successful Ingestion Indicators**
- ✅ All tests pass
- ✅ Expected record count inserted
- ✅ No constraint violations
- ✅ Data integrity checks pass
- ✅ Performance within acceptable range

### **Performance Benchmarks**
- **Congress Members**: 15-42 records/second
- **OpenStates People**: 300-2700 records/second
- **Congress Bills**: Target 50+ records/second

### **Quality Standards**
- **Zero duplicate primary keys**
- **All foreign keys valid**
- **Required fields not null**
- **Dates in correct format**

---

## 📝 **WORKFLOW CHECKLIST**

### **Pre-Ingestion**
- [ ] Database connection working
- [ ] API keys valid and not demo keys
- [ ] Required tables exist
- [ ] Test suite passes
- [ ] API connectivity confirmed

### **During Ingestion**
- [ ] Progress monitoring active
- [ ] Error handling working
- [ ] Rate limiting respected
- [ ] Batch sizes appropriate
- [ ] Logging enabled

### **Post-Ingestion**
- [ ] Record counts verified
- [ ] Data integrity checked
- [ ] Quality metrics met
- [ ] Performance benchmarks met
- [ ] Documentation updated

---

## 🔄 **CONTINUOUS IMPROVEMENT**

### **Workflow Optimization**
- **Automate validation steps**
- **Add comprehensive logging**
- **Implement retry logic**
- **Optimize batch sizes**
- **Add performance monitoring**

### **Documentation Updates**
- **Update procedures after changes**
- **Record lessons learned**
- **Add new error solutions**
- **Maintain workflow checklist**
- **Update success metrics**

---

## 🎯 **NEXT STEPS**

1. **Implement minimal bills ingestion script**
2. **Add automated validation**
3. **Create ingestion dashboard**
4. **Add performance monitoring**
5. **Implement backup procedures**

---

*Last Updated: 2025-11-26*
*Status: Working procedures documented*
*Priority: Fix bills ingestion workflow*
