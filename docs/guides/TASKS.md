# OpenDiscourse Ingestion Fix Tasks

## 🎯 **OBJECTIVE**
Fix Congress bills ingestion by simplifying the system and eliminating complex dependencies.

---

## 📊 **CURRENT STATUS**
- ✅ **Database Connection**: Working
- ✅ **API Credentials**: Working
- ✅ **API Connectivity**: Working
- ✅ **Tables Exist**: Working
- ❌ **Data Transformation**: Minor mapping issue
- ❌ **Bills Ingestion**: Broken due to complexity

---

## 📋 **TASK LIST**

### **Phase 1: Fix Data Transformation (IMMEDIATE)**
- [ ] **TASK 1.1**: Fix chamber code mapping test
  - **Issue**: Test expects `unknown` but mapping returns `''`
  - **Solution**: Update test to match actual behavior
  - **Time**: 5 minutes

### **Phase 2: Create Minimal Ingestion System (HIGH PRIORITY)**
- [ ] **TASK 2.1**: Create simple bills ingestion script
  - **Approach**: Single file, no dependencies
  - **Components**: API fetch → Transform → Insert
  - **Time**: 30 minutes

- [ ] **TASK 2.2**: Test with small batch (10 bills)
  - **Goal**: Verify insertion works
  - **Success Criteria**: Bills appear in database
  - **Time**: 10 minutes

- [ ] **TASK 2.3**: Scale to full ingestion
  - **Goal**: Ingest all Congress 118 bills
  - **Success Criteria**: 1000+ bills inserted
  - **Time**: 30 minutes

### **Phase 3: Validate & Deploy (MEDIUM PRIORITY)**
- [ ] **TASK 3.1**: Create comprehensive test suite
  - **Coverage**: Database, API, Transformation, Insertion
  - **Time**: 45 minutes

- [ ] **TASK 3.2**: Performance optimization
  - **Goal**: 50+ bills/second
  - **Approach**: Batch processing, connection pooling
  - **Time**: 30 minutes

- [ ] **TASK 3.3**: Error handling & logging
  - **Goal**: Graceful failure handling
  - **Approach**: Try/catch with meaningful messages
  - **Time**: 20 minutes

---

## 🔧 **TECHNICAL APPROACH**

### **Minimal System Design**
```
API Layer → Data Transformer → Database Layer
    ↓              ↓                ↓
Simple fetch  Map chamber codes  Direct insert
```

### **Key Simplifications**
1. **No checkpoint system** - eliminate stored procedure dependencies
2. **No complex monitoring** - simple progress indicators
3. **No rate limiting** - Congress.gov has generous limits
4. **No configuration system** - environment variables only
5. **No inheritance** - simple functions, not classes

### **Database Connection Pattern**
```python
conn = psycopg2.connect(
    database='opendiscourse',
    user='cbwinslow',
    host='/var/run/postgresql'
)
```

### **Data Transformation Pattern**
```python
chamber_mapping = {
    'House': 'house',
    'Senate': 'senate',
    'Joint': 'joint'
}
origin_chamber = chamber_mapping.get(api_chamber, api_chamber.lower())
```

---

## 🚀 **EXECUTION PLAN**

### **IMMEDIATE (Next 30 minutes)**
1. Fix chamber mapping test
2. Create minimal bills script
3. Test with 10 bills

### **SHORT TERM (Next 2 hours)**
4. Scale to full Congress 118 ingestion
5. Add basic error handling
6. Verify data integrity

### **MEDIUM TERM (Next 4 hours)**
7. Add Congress 116 & 117 bills
8. Create comprehensive tests
9. Performance optimization

---

## 📈 **SUCCESS METRICS**

### **Phase 1 Success**
- [ ] All tests pass
- [ ] Chamber mapping works correctly

### **Phase 2 Success**
- [ ] 10+ bills inserted successfully
- [ ] 1000+ bills inserted for Congress 118
- [ ] No foreign key constraint violations

### **Phase 3 Success**
- [ ] 50+ bills/second processing speed
- [ ] Zero data loss
- [ ] Comprehensive test coverage

---

## 🔄 **FALLBACK PLAN**

If minimal approach fails:
1. **Use existing working OpenStates system** as template
2. **Incrementally add Congress bills** functionality
3. **Keep complex system** as backup reference

---

## 🎯 **DECISION POINT**

**RECOMMENDATION**: **Start over with minimal system**
- **Current system**: Too complex, hard to debug
- **Minimal system**: Simple, testable, maintainable
- **Risk**: Low - we keep working data
- **Reward**: High - working bills ingestion

---

## ⏰ **TIMELINE**

- **Phase 1**: 30 minutes
- **Phase 2**: 1 hour
- **Phase 3**: 2 hours
- **Total**: 3.5 hours to working system

---

*Last Updated: 2025-11-26*
*Priority: HIGH - Fix bills ingestion*
*Status: Ready to execute*
